import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 실제 데이터 수집 모듈 (스텁 교체본)
# - KHOA 실측·예측 조위 (tide_observation 행 생성: 조위·잔차)
# - KMA 해양기상부이 (기압·풍속·풍향·돌풍·파고 UPDATE: 이미 있는 행에만 채움)
# - 버튼/배치가 부르는 단위: 관측소 1개, 어제+오늘 2일치
# - KMA는 보조라 실패해도 KHOA 결과를 살린다 (경고만 남김)
# ---------------------------------------------------------------------------

KHOA_TIDE_URL = (
    "https://apis.data.go.kr/1192136/surveyTideLevel/"
    "GetSurveyTideLevelApiService"
)
KMA_BUOY_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_buoy2.php"

# Repo B 관측소 코드 -> KHOA obsCode (2026-11-24 실제 API로 10/10 검증)
STATIONS = {
    "BUSAN": "DT_0005",
    "INCHEON": "DT_0001",
    "PYEONGTAEK": "DT_0002",
    "MOKPO": "DT_0007",
    "YEOSU": "DT_0016",
    "ULSAN": "DT_0020",
    "POHANG": "DT_0091",
    "BORYEONG": "DT_0025",
    "GUNSAN": "DT_0018",
    "JEJU": "DT_0004",
}

# 관측소 -> KMA 부이 코드 (평택·보령·군산은 22101 공용)
BUOY_MAPPING = {
    "BUSAN": "22104",
    "INCHEON": "22185",
    "ULSAN": "22189",
    "POHANG": "22106",
    "YEOSU": "22103",
    "PYEONGTAEK": "22101",
    "MOKPO": "22184",
    "BORYEONG": "22101",
    "GUNSAN": "22101",
    "JEJU": "22187",
}

REQUEST_DELAY_SEC = 0.3
MAX_RETRIES = 3

INSERT_SQL = (
    "INSERT INTO tide_observation "
    "(station_code, obs_time, tide_obs_cm, tide_pred_cm, residual_cm, "
    " air_pressure_hpa, wind_speed_ms, wind_dir_deg) "
    "VALUES (%s, %s, %s, %s, %s, NULL, NULL, NULL)"
)
DELETE_DAY_SQL = (
    "DELETE FROM tide_observation "
    "WHERE station_code = %s AND obs_time >= %s AND obs_time < %s"
)
UPDATE_WEATHER_SQL = (
    "UPDATE tide_observation "
    "SET air_pressure_hpa=%s, wind_speed_ms=%s, wind_dir_deg=%s, "
    "wind_gust_ms=%s, wave_height_m=%s "
    "WHERE station_code=%s AND obs_time=%s"
)


class KhoaError(RuntimeError):
    def __init__(self, message, fatal=False):
        super().__init__(message)
        self.fatal = fatal


# ---------------------------------------------------------------------------
# DB 접속 정보: DB_URL(JDBC) 우선, 없으면 개별 변수
# ---------------------------------------------------------------------------

def parse_jdbc_url(url):
    m = re.match(r"jdbc:mariadb://(\[[^\]]+\]|[^/:?]+)(?::(\d+))?/([^?]+)", url.strip())
    if not m:
        return None
    host, port, dbname = m.group(1), m.group(2), m.group(3)
    host = host.strip("[]")
    return host, int(port) if port else 3306, dbname


def get_db_config():
    jdbc = os.environ.get("DB_URL", "")
    if jdbc:
        parsed = parse_jdbc_url(jdbc)
        if parsed:
            host, port, dbname = parsed
            return {
                "host": host, "port": port, "database": dbname,
                "user": os.environ.get("DB_USER") or os.environ.get("SURGE_DB_USER") or "surge",
                "password": os.environ.get("DB_PASSWORD") or os.environ.get("SURGE_DB_PASSWORD") or "",
            }
    host = os.environ.get("DB_HOST") or os.environ.get("SURGE_DB_HOST") or "localhost"
    port = int(os.environ.get("DB_PORT") or os.environ.get("SURGE_DB_PORT") or 3306)
    dbname = os.environ.get("DB_NAME") or os.environ.get("SURGE_DB_NAME") or "storm_surge_team"
    return {
        "host": host.strip("[]"), "port": port, "database": dbname,
        "user": os.environ.get("DB_USER") or os.environ.get("SURGE_DB_USER") or "surge",
        "password": os.environ.get("DB_PASSWORD") or os.environ.get("SURGE_DB_PASSWORD") or "",
    }


def connect_db(cfg):
    try:
        import pymysql
    except ImportError:
        raise RuntimeError("pymysql이 없습니다. pip install pymysql 후 FastAPI를 재시작하세요.")
    return pymysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"],
        password=cfg["password"], database=cfg["database"],
        charset="utf8mb4", autocommit=False,
    )


# ---------------------------------------------------------------------------
# KHOA 조위
# ---------------------------------------------------------------------------

def _http_get_json(url, params, timeout=30):
    safe_params = dict(params)
    if "serviceKey" in safe_params:
        safe_params["serviceKey"] = urllib.parse.unquote(safe_params["serviceKey"])
    query = urllib.parse.urlencode(safe_params)
    req = urllib.request.Request(
        url + "?" + query,
        headers={"User-Agent": "disaster_predict_platform collector"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return exc.code, body


def _backoff(attempt):
    if attempt < MAX_RETRIES:
        time.sleep(2 ** attempt)


def fetch_tide_day(api_key, obs_code, day):
    params = {
        "serviceKey": api_key,
        "type": "json",
        "obsCode": obs_code,
        "reqDate": day.strftime("%Y%m%d"),
        "min": 60,
        "numOfRows": 100,
        "pageNo": 1,
    }
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            status, body = _http_get_json(KHOA_TIDE_URL, params)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = KhoaError(f"네트워크 오류: {exc}")
            _backoff(attempt)
            continue
        if status == 429:
            last_err = KhoaError("HTTP 429 - 일일 호출 한도 초과 가능성")
            _backoff(attempt)
            continue
        if status >= 500:
            last_err = KhoaError(f"HTTP {status} - KHOA 서버 오류")
            _backoff(attempt)
            continue
        if status != 200:
            raise KhoaError(f"HTTP {status}: {body[:300]}", fatal=True)
        return parse_tide_response(body)
    raise last_err or KhoaError("알 수 없는 호출 실패")


def parse_tide_response(body):
    text = body.strip()
    if text.startswith("<"):
        m = re.search(r"<returnAuthMsg>(.*?)</returnAuthMsg>", text)
        msg = m.group(1) if m else text[:300]
        raise KhoaError(f"KHOA 오류 응답(XML): {msg}", fatal=True)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise KhoaError(f"JSON 파싱 실패: {exc} / 본문 앞부분: {text[:200]}", fatal=True)
    root = data.get("response", data)
    header = root.get("header", {}) if isinstance(root, dict) else {}
    code = str(header.get("resultCode", "00"))
    if code not in ("00", "0"):
        msg = header.get("resultMsg", "")
        fatal = code in ("10", "11", "12", "20", "21", "22", "30", "31", "32", "33")
        raise KhoaError(f"KHOA resultCode={code}: {msg}", fatal=fatal)
    body_obj = root.get("body", {}) if isinstance(root, dict) else {}
    items = body_obj.get("items", {}) if isinstance(body_obj, dict) else {}
    if isinstance(items, dict):
        items = items.get("item", [])
    if isinstance(items, dict):
        items = [items]
    if not items:
        return []
    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        obs_time = _parse_obs_time(_pick(it, "obsrvnDt", "obsrvn_dt", "obsTime", "recordTime"))
        if obs_time is None:
            continue
        obs = _to_float(_pick(it, "bscTdlvHgt", "tideObs", "obsTide"))
        pred = _to_float(_pick(it, "tdlvHgt", "tidePred", "predTide"))
        rows.append((obs_time, obs, pred))
    rows.sort(key=lambda r: r[0])
    return rows


def _pick(item, *names):
    for name in names:
        if name in item and item[name] not in (None, ""):
            return item[name]
    return None


def _parse_obs_time(value):
    if value is None:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _to_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if text in ("", "-", "null", "None"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def replace_day(conn, station_code, day, rows):
    """하루 구간을 통째로 교체한다 (삭제+삽입, 한 트랜잭션). rows가 비면 건드리지 않음."""
    if not rows:
        return 0, 0
    day_start = datetime(day.year, day.month, day.day)
    day_end = day_start + timedelta(days=1)
    values = []
    for obs_time, obs, pred in rows:
        residual = None
        if obs is not None and pred is not None:
            residual = round(obs - pred, 2)
        values.append((station_code, obs_time, obs, pred, residual))
    with conn.cursor() as cur:
        cur.execute(DELETE_DAY_SQL, (station_code, day_start, day_end))
        deleted = cur.rowcount
        cur.executemany(INSERT_SQL, values)
        inserted = cur.rowcount if cur.rowcount and cur.rowcount > 0 else len(values)
    conn.commit()
    return deleted, inserted


# ---------------------------------------------------------------------------
# KMA 부이 (기압·풍속·풍향 UPDATE — KHOA 행이 먼저 있어야 함)
# ---------------------------------------------------------------------------

def fetch_buoy_day(api_key, stn, day, timeout=30):
    params = {
        "tm1": day.strftime("%Y%m%d0000"),
        "tm2": day.strftime("%Y%m%d2300"),
        "stn": stn,
        "authKey": api_key,
        "disp": "1",
    }
    url = KMA_BUOY_URL + "?" + urllib.parse.urlencode(params)
    data = None
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except Exception as exc:
            last_err = exc
            logger.warning("KMA 재시도 %d/3 (%s %s): %s", attempt + 1, stn, day, exc)
            time.sleep(5)
    if data is None:
        raise RuntimeError(f"KMA 호출 실패 ({stn} {day}): {last_err}")
    rows = []
    for it in data:
        tm = it.get("TM", "")
        if not tm.endswith("00"):
            continue
        rows.append({
            "tm": tm,
            "wd": it.get("WD1"),
            "ws": it.get("WS1"),
            "gst": it.get("WS1_GST"),
            "pa": it.get("PA"),
            "wh": it.get("WH_SIG"),
        })
    return rows


def update_weather_day(conn, station_code, rows):
    """부이 행을 tide_observation 기상 컬럼에 UPDATE. 갱신된 행 수 반환."""
    updated = 0
    with conn.cursor() as cur:
        for row in rows:
            ts = f"{row['tm'][:4]}-{row['tm'][4:6]}-{row['tm'][6:8]} {row['tm'][8:10]}:{row['tm'][10:12]}:00"
            cur.execute(
                UPDATE_WEATHER_SQL,
                (row["pa"], row["ws"], row["wd"], row["gst"], row["wh"], station_code, ts),
            )
            updated += cur.rowcount
    conn.commit()
    return updated


# ---------------------------------------------------------------------------
# 수집기 본체
# ---------------------------------------------------------------------------

class DataCollector:
    """
    KHOA 실측·예측 조위 + KMA 해양기상부이 실제 수집 모듈.
    - API 키: KHOA_API_KEY 또는 DATA_GO_KR_API_KEY, KMA_API_KEY (.env)
    - 관측소 1개, 어제+오늘 2일치를 적재한다.
    - KHOA가 행을 만들고, KMA가 그 행의 기상 컬럼(기압·풍속·풍향·돌풍·파고)을 채운다 (순서 중요).
    - KMA 실패는 경고를 남기고 넘어간다. KHOA가 핵심 데이터다.
    """

    def __init__(self):
        self.khoa_api_key = os.getenv("KHOA_API_KEY") or os.getenv("DATA_GO_KR_API_KEY", "")
        self.kma_api_key = os.getenv("KMA_API_KEY", "")

    def collect_station_data(self, station_id: str) -> Dict[str, Any]:
        station = (station_id or "").upper()
        now = datetime.now()
        today = date.today()
        days = [today - timedelta(days=1), today]
        result: Dict[str, Any] = {
            "station_id": station,
            "collected_at": now.isoformat(),
            "status": "SUCCESS",
            "khoa": {"inserted": 0, "days": []},
            "kma": {"updated": 0, "status": "SKIPPED"},
        }
        if station not in STATIONS:
            result["status"] = "FAILED"
            result["error"] = f"알 수 없는 관측소: {station_id}"
            logger.error("collect_station_data: %s", result["error"])
            return result
        if not self.khoa_api_key:
            result["status"] = "FAILED"
            result["error"] = "KHOA API 키가 없습니다 (.env KHOA_API_KEY)"
            logger.error("collect_station_data %s: %s", station, result["error"])
            return result

        try:
            cfg = get_db_config()
            conn = connect_db(cfg)
        except Exception as exc:
            result["status"] = "FAILED"
            result["error"] = f"DB 접속 실패: {exc}"
            logger.error("collect_station_data %s: %s", station, result["error"])
            return result

        try:
            # 1. KHOA 조위 (행 생성)
            obs_code = STATIONS[station]
            for day in days:
                try:
                    rows = fetch_tide_day(self.khoa_api_key, obs_code, day)
                except KhoaError as exc:
                    logger.error("KHOA %s %s 실패: %s", station, day, exc)
                    result["status"] = "PARTIAL"
                    result.setdefault("errors", []).append(f"KHOA {day}: {exc}")
                    if exc.fatal:
                        break
                    continue
                if not rows:
                    logger.warning("KHOA %s %s 빈 응답 (DB 건드리지 않음)", station, day)
                    continue
                deleted, inserted = replace_day(conn, station, day, rows)
                result["khoa"]["inserted"] += inserted
                result["khoa"]["days"].append(str(day))
                logger.info("KHOA %s %s: %d행 적재 (기존 %d행 교체)", station, day, inserted, deleted)
                time.sleep(REQUEST_DELAY_SEC)

            # 2. KMA 부이 (기상 컬럼 UPDATE — 실패해도 KHOA 결과는 유지)
            if not self.kma_api_key:
                result["kma"]["status"] = "NO_KEY"
                logger.warning("KMA %s: 키가 없어 건너뜀", station)
            else:
                stn = BUOY_MAPPING.get(station)
                if not stn:
                    result["kma"]["status"] = "NO_BUOY"
                else:
                    try:
                        total_updated = 0
                        for day in days:
                            rows = fetch_buoy_day(self.kma_api_key, stn, day)
                            total_updated += update_weather_day(conn, station, rows)
                            time.sleep(1)
                        result["kma"]["updated"] = total_updated
                        result["kma"]["status"] = "SUCCESS"
                        logger.info("KMA %s: %d행 기상 업데이트", station, total_updated)
                    except Exception as exc:
                        result["kma"]["status"] = "FAILED"
                        result["kma"]["error"] = str(exc)
                        if result["status"] == "SUCCESS":
                            result["status"] = "PARTIAL"
                        logger.warning("KMA %s 실패 (KHOA 결과는 유지): %s", station, exc)
        except Exception as exc:
            result["status"] = "FAILED"
            result["error"] = str(exc)
            logger.error("collect_station_data %s 실패: %s", station, exc)
        finally:
            try:
                conn.close()
            except Exception:
                pass

        logger.info("collect_station_data %s 완료: %s", station, result["status"])
        return result
