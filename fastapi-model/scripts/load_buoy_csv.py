import os, re
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
import pymysql

# 조위 지점 -> 부이 코드
# 부산은 거제도 부이를 빌려 써. 나머지는 같은 이름 부이야.
# 평택·목포·보령·군산·제주는 같은 이름 부이가 없어서 일단 빼뒀어. 팀이랑 정해야 해.
MAPPING = {
    "BUSAN": "22104",
    "INCHEON": "22185",
    "ULSAN": "22189",
    "POHANG": "22106",
    "YEOSU": "22103",
}

def load_env():
    # 루트 .env 읽기
    root = Path(__file__).resolve().parent.parent.parent / ".env"
    if root.is_file():
        for line in open(root, encoding="utf-8-sig"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip(); v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

def get_db():
    load_env()
    url = os.environ.get("DB_URL", "")
    m = re.match(r"jdbc:mariadb://([^/:?]+)(?::(\d+))?/([^?]+)", url)
    if m:
        host, port, db = m.group(1), int(m.group(2) or 3306), m.group(3)
    else:
        host, port, db = "localhost", 3306, "storm_surge_team"
    return pymysql.connect(
        host=host, port=port, user=os.environ.get("DB_USER", "surge"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=db, charset="utf8mb4", autocommit=False,
    )

UPDATE_SQL = """
UPDATE tide_observation
SET air_pressure_hpa=%s, wind_speed_ms=%s, wind_dir_deg=%s
WHERE station_code=%s AND obs_time=%s
"""

conn = get_db()
print(f"DB 연결됨")

for station, code in MAPPING.items():
    path = Path(f"data/buoy_{code}_1yr.csv")
    # scripts 폴더에서 실행하면 data 폴더는 fastapi-model/data야
    if not path.is_file():
        path = Path(__file__).resolve().parent.parent / f"data/buoy_{code}_1yr.csv"
    if not path.is_file():
        print(f"{station}: 부이 파일 없음 {path}")
        continue
    df = pd.read_csv(path)
    # 컬럼이 한글일 수도 있어서 위치로 읽어
    # timestamp, wind_speed, wind_dir, wind_gust, pressure, wave 순서가 아닐 수 있으니 이름으로 찾기
    print(f"{station} ({code}): {len(df)}행 읽음, 컬럼 {list(df.columns)}")
    updated = 0
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            ts = pd.to_datetime(row["timestamp"])
            # 컬럼 이름이 다르면 여기서 바꿔줘
            pa = row.get("air_pressure_hpa")
            ws = row.get("wind_speed_ms")
            wd = row.get("wind_dir_deg")
            if pd.isna(pa) and pd.isna(ws) and pd.isna(wd):
                continue
            cur.execute(UPDATE_SQL, (
                None if pd.isna(pa) else float(pa),
                None if pd.isna(ws) else float(ws),
                None if pd.isna(wd) else float(wd),
                station, ts.to_pydatetime(),
            ))
            updated += cur.rowcount
    conn.commit()
    print(f"{station}: {updated}행 업데이트됨")

conn.close()
print("완료")