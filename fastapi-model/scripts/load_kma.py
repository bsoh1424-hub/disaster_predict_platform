import os, json, urllib.request, urllib.parse, time
from pathlib import Path
from datetime import date, timedelta
import pymysql

# 조위 지점 -> 부이 코드
MAPPING = {
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

def load_env():
    root = Path(__file__).resolve().parent.parent.parent / ".env"
    for line in open(root, encoding="utf-8-sig"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v

load_env()
KEY = os.environ.get("KMA_API_KEY", "")

def fetch_day(stn, day):
    tm1 = day.strftime("%Y%m%d0000")
    tm2 = day.strftime("%Y%m%d2300")
    params = {
        "tm1": tm1, "tm2": tm2,
        "stn": stn, "authKey": KEY, "disp": "1",
    }
    url = "https://apihub.kma.go.kr/api/typ01/url/kma_buoy2.php?" + urllib.parse.urlencode(params)
    data = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"재시도 {attempt+1}/3: {e}")
            time.sleep(5)
    if data is None:
        print(f"{stn} {day} 실패, 건너뜀")
        return []
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

def get_db():
    import re
    url = os.environ.get("DB_URL", "")
    m = re.match(r"jdbc:mariadb://([^/:?]+)(?::(\d+))?/([^?]+)", url)
    host, port, db = m.group(1), int(m.group(2) or 3306), m.group(3)
    return pymysql.connect(
        host=host, port=port, user=os.environ.get("DB_USER", "surge"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=db, charset="utf8mb4", autocommit=False,
    )

# 4일치: 11월 22, 23, 24, 25일 (오늘 포함)
days = [date.today() - timedelta(days=i) for i in (3, 2, 1, 0)]

conn = get_db()
for day in days:
    print(f"대상: {day}")
    for station, stn in MAPPING.items():
        rows = fetch_day(stn, day)
        time.sleep(1)
        print(f"{station} ({stn}): {len(rows)}행 받음")
        updated = 0
        with conn.cursor() as cur:
            for row in rows:
                ts = f"{row['tm'][:4]}-{row['tm'][4:6]}-{row['tm'][6:8]} {row['tm'][8:10]}:{row['tm'][10:12]}:00"
                cur.execute(
                    "UPDATE tide_observation SET air_pressure_hpa=%s, wind_speed_ms=%s, wind_dir_deg=%s, wind_gust_ms=%s, wave_height_m=%s WHERE station_code=%s AND obs_time=%s",
                    (row["pa"], row["ws"], row["wd"], row["gst"], row["wh"], station, ts),
                )
                updated += cur.rowcount
        conn.commit()
        print(f"{station}: {updated}행 업데이트됨")

conn.close()
print("완료")