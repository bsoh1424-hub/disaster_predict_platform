#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
load_khoa.py - KHOA 실측 조위 적재 스크립트 (Repo B: disaster_predict_platform 전용)

공공데이터포털 "해양수산부 국립해양조사원_조위관측소 실측·예측 조위 조회"
(data.go.kr 데이터셋 15142507) API에서 1시간 간격 조위를 받아
Repo B 전용 MariaDB(storm_surge_team)의 tide_observation 테이블에 넣는다.

Repo B 테이블 컬럼 (Spring 엔티티 TideObservation 기준):
    station_code, obs_time, tide_obs_cm, tide_pred_cm, residual_cm,
    air_pressure_hpa, wind_speed_ms, wind_dir_deg

주의:
  - 이 조위 API는 조위만 준다. 기압·풍속·풍향은 이 API에 없어서 NULL로 남긴다.
    (기압·풍속이 필요하면 KMA 쪽 별도 API를 붙여야 한다.)
  - Repo A(storm-surge-platform)의 tide_observation과는 컬럼명이 완전히 다르다.
    이 스크립트는 Repo B 전용이다. Repo A DB(storm_surge)에 넣지 말 것.

놓는 위치 (권장):
    C:\\Users\\it\\disaster_predict_platform\\fastapi-model\\scripts\\load_khoa.py
    (어느 폴더에서 실행해도 동작한다. .env 탐색 경로는 아래 load_env_files 참고)

실행 예:
    python load_khoa.py --date 2026-11-23
    python load_khoa.py --from 2026-11-20 --to 2026-11-23
    python load_khoa.py --from 2026-11-20 --to 2026-11-23 --station BUSAN
    python load_khoa.py --date 2026-11-23 --dry-run

필요한 것:
    - Python 3.10+
    - pymysql  (pip install pymysql)  -- HTTP는 표준 라이브러리만 쓴다
    - .env 에 KHOA_API_KEY (또는 DATA_GO_KR_API_KEY)와 DB 접속 정보

멱등성:
    tide_observation에는 (station_code, obs_time) 유니크 키가 없다
    (PK는 자동증가 id 하나뿐). 그래서 관측소·날짜 단위로
    "API 수신 성공 -> 그 구간 기존 행 삭제 -> 새 행 삽입"을 한 트랜잭션으로
    처리한다. 같은 날짜를 다시 실행해도 중복이 생기지 않고,
    Spring 시드(DataInitService)가 넣은 가짜 BUSAN 행도 적재한 날짜
    구간에서는 실제 값으로 교체된다. API 수신에 실패하면 삭제하지 않는다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

KHOA_TIDE_URL = (
    "https://apis.data.go.kr/1192136/surveyTideLevel/"
    "GetSurveyTideLevelApiService"
)

# Repo B 관측소 코드 -> KHOA obsCode
# 2026-11-24 실제 KHOA API 응답으로 10/10 검증 완료 (관측소명 대조,
# 2026-11-23 기준 하루 24행씩 수신 확인). 위도·경도는 API 응답 실측값이며
# Spring 시드(DataInitService)의 근사 좌표와 조금 다르다 - 대조용으로만 둔다.
STATIONS = {
    "BUSAN":     {"obs_code": "DT_0005", "name": "부산", "lat": 35.09638, "lng": 129.03527},
    "INCHEON":   {"obs_code": "DT_0001", "name": "인천", "lat": 37.45194, "lng": 126.59222},
    "PYEONGTAEK": {"obs_code": "DT_0002", "name": "평택", "lat": 36.96694, "lng": 126.82277},
    "MOKPO":     {"obs_code": "DT_0007", "name": "목포", "lat": 34.77972, "lng": 126.37555},
    "YEOSU":     {"obs_code": "DT_0016", "name": "여수", "lat": 34.74722, "lng": 127.76555},
    "ULSAN":     {"obs_code": "DT_0020", "name": "울산", "lat": 35.50194, "lng": 129.38722},
    "POHANG":    {"obs_code": "DT_0091", "name": "포항", "lat": 36.05177, "lng": 129.37627},
    "BORYEONG":  {"obs_code": "DT_0025", "name": "보령", "lat": 36.40638, "lng": 126.48611},
    "GUNSAN":    {"obs_code": "DT_0018", "name": "군산", "lat": 35.97555, "lng": 126.56305},
    "JEJU":      {"obs_code": "DT_0004", "name": "제주", "lat": 33.52750, "lng": 126.54305},
}

DAILY_QUOTA_DEV = 10000  # data.go.kr 개발계정 일일 한도 (KHOA)
REQUEST_DELAY_SEC = 0.3  # 호출 사이 간격 (한도·서버 부담 완화)
MAX_RETRIES = 3          # 429 / 5xx / 네트워크 오류 재시도 횟수

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


# ---------------------------------------------------------------------------
# .env 로딩 (python-dotenv가 없어도 동작하게 직접 파싱한다)
# ---------------------------------------------------------------------------

def _parse_env_file(path):
    """KEY=VALUE 줄만 읽는다. 이미 있는 환경변수는 덮지 않는다."""
    try:
        with open(path, encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


def load_env_files(script_dir):
    """탐색 순서: 스크립트 옆 .env -> 부모(fastapi-model) .env ->
    저장소 루트 .env -> 현재 작업 폴더 .env. 먼저 읽힌 값이 우선한다."""
    candidates = [
        script_dir / ".env",
        script_dir.parent / ".env",
        script_dir.parent.parent / ".env",
        script_dir.parent.parent.parent / ".env",
    ]
    try:
        from pathlib import Path
        candidates.append(Path.cwd() / ".env")
    except Exception:
        pass
    loaded = []
    for path in candidates:
        if path.is_file():
            _parse_env_file(path)
            loaded.append(str(path))
    return loaded


def get_api_key():
    return os.environ.get("KHOA_API_KEY") or os.environ.get("DATA_GO_KR_API_KEY") or ""


# ---------------------------------------------------------------------------
# DB 접속 정보: DB_URL(JDBC) 우선, 없으면 개별 변수
# ---------------------------------------------------------------------------

def parse_jdbc_url(url):
    """jdbc:mariadb://host:port/dbname?params -> (host, port, dbname)"""
    m = re.match(r"jdbc:mariadb://(\[[^\]]+\]|[^/:?]+)(?::(\d+))?/([^?]+)", url.strip())
    if not m:
        return None
    host, port, dbname = m.group(1), m.group(2), m.group(3)
    host = host.strip("[]")  # [::1] 같은 IPv6 표기 정리
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
    host = (os.environ.get("DB_HOST") or os.environ.get("SURGE_DB_HOST")
            or "localhost")
    port = int(os.environ.get("DB_PORT") or os.environ.get("SURGE_DB_PORT") or 3306)
    dbname = (os.environ.get("DB_NAME") or os.environ.get("SURGE_DB_NAME")
              or "storm_surge_team")
    return {
        "host": host.strip("[]"), "port": port, "database": dbname,
        "user": os.environ.get("DB_USER") or os.environ.get("SURGE_DB_USER") or "surge",
        "password": os.environ.get("DB_PASSWORD") or os.environ.get("SURGE_DB_PASSWORD") or "",
    }


# ---------------------------------------------------------------------------
# KHOA API 호출
# ---------------------------------------------------------------------------

class KhoaError(RuntimeError):
    """KHOA API 오류. fatal=True면 재시도·계속 진행이 의미 없는 오류."""

    def __init__(self, message, fatal=False):
        super().__init__(message)
        self.fatal = fatal


def _http_get_json(url, params, timeout=30):
    """GET 한 번. (상태코드, 본문 텍스트)를 돌려준다."""
    # serviceKey는 포털에서 받은 형태 그대로(인코딩본/원본) 넣어도 되게
    # 한 번 디코딩한 뒤 urlencode로 다시 인코딩한다 (이중 인코딩 방지).
    safe_params = dict(params)
    if "serviceKey" in safe_params:
        safe_params["serviceKey"] = urllib.parse.unquote(safe_params["serviceKey"])
    query = urllib.parse.urlencode(safe_params)
    req = urllib.request.Request(
        url + "?" + query,
        headers={"User-Agent": "load_khoa.py (disaster_predict_platform)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return exc.code, body


def fetch_tide_day(api_key, obs_code, day):
    """관측소 하루치(1시간 간격, 보통 24행)를 받아 파싱된 행 목록으로 돌려준다.
    각 행: (obs_time datetime, tide_obs_cm float|None, tide_pred_cm float|None)
    """
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


def _backoff(attempt):
    if attempt < MAX_RETRIES:
        time.sleep(2 ** attempt)  # 2초, 4초


def parse_tide_response(body):
    """data.go.kr JSON 응답 파싱. 오류 응답(XML 포함)이면 KhoaError."""
    text = body.strip()
    if text.startswith("<"):
        # JSON을 요청해도 오류인 경우 XML(OpenAPI_ServiceResponse)로 오는 경우가 있다
        m = re.search(r"<returnAuthMsg>(.*?)</returnAuthMsg>", text)
        msg = m.group(1) if m else text[:300]
        raise KhoaError(f"KHOA 오류 응답(XML): {msg}", fatal=True)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise KhoaError(f"JSON 파싱 실패: {exc} / 본문 앞부분: {text[:200]}", fatal=True)

    # 표준 봉투 {response: {header, body}} 와 flat {header, body} 둘 다 수용
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
    """'-', '', None 같은 결측 표기는 None으로."""
    if value is None:
        return None
    text = str(value).strip()
    if text in ("", "-", "null", "None"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# DB 적재
# ---------------------------------------------------------------------------

def connect_db(cfg):
    try:
        import pymysql
    except ImportError:
        raise SystemExit(
            "pymysql이 없습니다. 먼저 설치하세요:  pip install pymysql\n"
            "(Anaconda 터미널과 시스템 Python 3.12 중, 이 스크립트를 실행할 "
            "Python에 설치해야 합니다.)"
        )
    if not cfg["password"]:
        print("[경고] DB 비밀번호가 비어 있습니다. .env의 DB_PASSWORD를 확인하세요.",
              file=sys.stderr)
    return pymysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"],
        password=cfg["password"], database=cfg["database"],
        charset="utf8mb4", autocommit=False,
    )


def replace_day(conn, station_code, day, rows):
    """하루 구간을 통째로 교체한다 (삭제+삽입, 한 트랜잭션).
    rows가 비어 있으면 DB를 건드리지 않는다. (삭제 행 수, 삽입 행 수) 반환."""
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


def verify_counts(conn, station_codes, start_day, end_day):
    """적재 후 확인: 관측소별 행 수와 기간을 조회해 표로 돌려준다."""
    start_dt = datetime(start_day.year, start_day.month, start_day.day)
    end_dt = datetime(end_day.year, end_day.month, end_day.day) + timedelta(days=1)
    result = {}
    with conn.cursor() as cur:
        for code in station_codes:
            cur.execute(
                "SELECT COUNT(*), MIN(obs_time), MAX(obs_time) "
                "FROM tide_observation "
                "WHERE station_code = %s AND obs_time >= %s AND obs_time < %s",
                (code, start_dt, end_dt),
            )
            cnt, mn, mx = cur.fetchone()
            result[code] = (cnt, mn, mx)
    return result


# ---------------------------------------------------------------------------
# 날짜·인자 처리
# ---------------------------------------------------------------------------

def daterange(start, end):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def parse_day(text, label):
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit(f"{label} 날짜 형식이 잘못됐습니다: {text!r} (YYYY-MM-DD로 주세요)")


def build_parser():
    p = argparse.ArgumentParser(
        description="KHOA 실측 조위를 storm_surge_team.tide_observation에 적재",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--date", help="하루만 적재 (YYYY-MM-DD). --from/--to와 함께 쓰지 않는다")
    p.add_argument("--from", dest="date_from", help="구간 시작일 (YYYY-MM-DD)")
    p.add_argument("--to", dest="date_to", help="구간 종료일 (YYYY-MM-DD, 포함)")
    p.add_argument("--station", default="ALL",
                   help="관측소 코드 하나 (예: BUSAN) 또는 ALL")
    p.add_argument("--dry-run", action="store_true",
                   help="API 호출·파싱까지만 하고 DB에는 넣지 않는다")
    return p


def resolve_days(args):
    today = date.today()
    if args.date:
        if args.date_from or args.date_to:
            raise SystemExit("--date는 --from/--to와 함께 쓸 수 없습니다")
        day = parse_day(args.date, "--date")
        return day, day
    if bool(args.date_from) != bool(args.date_to):
        raise SystemExit("--from과 --to는 같이 줘야 합니다")
    if args.date_from:
        start = parse_day(args.date_from, "--from")
        end = parse_day(args.date_to, "--to")
        if end < start:
            raise SystemExit("--to가 --from보다 빠릅니다")
        return start, end
    yesterday = today - timedelta(days=1)
    return yesterday, yesterday  # 기본값: 어제 하루 (실측이 다 차 있는 날)


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main(argv=None):
    from pathlib import Path
    script_dir = Path(__file__).resolve().parent
    loaded_env = load_env_files(script_dir)

    args = build_parser().parse_args(argv)
    start_day, end_day = resolve_days(args)

    station_arg = args.station.upper()
    if station_arg == "ALL":
        station_codes = list(STATIONS.keys())
    elif station_arg in STATIONS:
        station_codes = [station_arg]
    else:
        raise SystemExit(
            f"알 수 없는 관측소: {args.station!r} "
            f"(가능한 값: ALL, {', '.join(STATIONS)})"
        )

    days = list(daterange(start_day, end_day))
    total_calls = len(days) * len(station_codes)
    print(f"대상: {start_day} ~ {end_day} ({len(days)}일) x "
          f"{len(station_codes)}개 관측소 = API {total_calls}회 호출")
    if total_calls > DAILY_QUOTA_DEV:
        print(f"[경고] 개발계정 일일 한도({DAILY_QUOTA_DEV:,}회)를 넘는 "
              f"호출 수입니다. 날짜 구간을 나눠서 실행하세요.", file=sys.stderr)
    if end_day >= date.today():
        print("[참고] 오늘·미래 날짜는 실측이 비어 예측만 오거나 행이 적을 수 있습니다.")

    api_key = get_api_key()
    if not api_key:
        raise SystemExit(
            "KHOA API 키가 없습니다. .env에 KHOA_API_KEY=... (또는 "
            "DATA_GO_KR_API_KEY=...)를 넣으세요.\n"
            f"(.env 탐색 위치: 스크립트 폴더, 그 부모들, 현재 폴더 / "
            f"읽은 파일: {loaded_env or '없음'})"
        )

    conn = None
    cfg = None
    if not args.dry_run:
        cfg = get_db_config()
        print(f"DB: {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']}")
        if cfg["database"] == "storm_surge":
            print("[경고] DB 이름이 storm_surge입니다. Repo A DB일 수 있습니다. "
                  "Repo B는 storm_surge_team을 써야 합니다.", file=sys.stderr)
        conn = connect_db(cfg)

    total_inserted = 0
    failures = []
    try:
        for code in station_codes:
            obs_code = STATIONS[code]["obs_code"]
            for day in days:
                label = f"{code}({obs_code}) {day}"
                try:
                    rows = fetch_tide_day(api_key, obs_code, day)
                except KhoaError as exc:
                    print(f"[실패] {label}: {exc}")
                    failures.append((label, str(exc)))
                    if exc.fatal:
                        print("  -> 키/권한 계열 오류로 보입니다. 중단합니다.")
                        raise SystemExit(1)
                    continue
                if not rows:
                    print(f"[빈응답] {label}: 0행 (DB는 건드리지 않음)")
                    failures.append((label, "0행"))
                    continue
                if args.dry_run:
                    sample = rows[0]
                    print(f"[dry-run] {label}: {len(rows)}행, 첫 행 "
                          f"{sample[0]} obs={sample[1]} pred={sample[2]}")
                    total_inserted += len(rows)
                else:
                    try:
                        deleted, inserted = replace_day(conn, code, day, rows)
                    except Exception as exc:  # DB 오류 시 그 구간만 롤백
                        conn.rollback()
                        print(f"[DB실패] {label}: {exc}")
                        failures.append((label, f"DB: {exc}"))
                        continue
                    total_inserted += inserted
                    extra = f" (기존 {deleted}행 교체)" if deleted else ""
                    print(f"[적재] {label}: {inserted}행{extra}")
                time.sleep(REQUEST_DELAY_SEC)

        if conn is not None:
            print("\n== 적재 후 확인 (DB 조회) ==")
            counts = verify_counts(conn, station_codes, start_day, end_day)
            for code in station_codes:
                cnt, mn, mx = counts[code]
                print(f"  {code:<10} {cnt:>5}행  {mn} ~ {mx}")
    finally:
        if conn is not None:
            conn.close()

    mode = "수신" if args.dry_run else "적재"
    print(f"\n완료: 총 {total_inserted}행 {mode}, 실패 {len(failures)}건")
    if failures:
        for label, reason in failures:
            print(f"  - {label}: {reason}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
