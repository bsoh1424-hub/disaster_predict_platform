# surge_pipeline.py - 폭풍해일 잔차 예측 자동 파이프라인 (LSTM.html 기준)
# train_surge.py를 매일 자동으로 돌리는 버전이야. 챔피언 vs 챌린저 경쟁까지 해.
# sample_model_pipeline.py를 새 스펙에 맞게 바꾼 거야. (샘플 파이프라인은 그대로 둬.)
#
# ============================================================
# ★ 새 스펙 (LSTM.html 기준) - 5곳이 이미 채워져 있어 ★
#   1) [X] feature_cols - 7개
#      tide_obs_cm, residual_cm, air_pressure_hpa, wind_speed_ms,
#      wind_gust_ms, wind_dir_deg, wave_height_m
#   2) [T] target - 편차(residual_cm) 2개: +12h, +24h
#      residual = 실측조위 - 예측 천문조
#   3) [t 공식] 위험 판정 - 이 파일에서는 안 해.
#      편차만 예측하고, 전체 조위(천문조 + 편차)랑 183/214cm 비교는
#      FastAPI 쪽에서 해. (exceed_probability도 FastAPI에서 계산해.)
#   4) [모델] SurgeLSTM - input_size=7, hidden_size=64, 1층, 출력 2개
#   5) [설정] WINDOW=72, EPOCHS=100, 챔피언 32 / 챌린저 64
#      챌린저는 챔피언이랑 배치만 다르게 해.
# ============================================================
#
# 데이터: merged_busan_1yr.csv (1년 단위, 1시간 간격, 부산 먼저)
# 실행: python surge_pipeline.py (매일 06:10 스케줄러가 돌려)
#   스케줄러 등록은 run_surge_daily.bat 참고해.
#
# ★ 이전 리뷰에서 고친 것 (sample_model_pipeline.py의 지적) ★
#   1) 교체(스왑) 리셋 문제 - 고쳤어. 이제 교체하면 registry에 새 배치 크기를 저장하고,
#      다음 실행 때 그 크기를 읽어와. 그래서 교체가 다음 날 리셋되지 않아.
#   2) rmse 컬럼이 mae랑 같던 문제 - 고쳤어. 이제 진짜 RMSE를 계산해.
#   3) 배치 셔플 없음 - 아직 안 고쳤어. (작은 문제라 나중에.)
#
# ★ 챔피언 고정 수정 (2026-11-25) - surge_pipeline.py와 다른 점 ★
#   원래 코드는 매번 챔피언도 챌린저도 둘 다 처음부터 다시 훈련했어.
#   이 파일은 챔피언은 result/champion.pt가 있으면 그대로 불러오고,
#   챌린저만 새로 훈련해. champion.pt가 없을 때만 처음 한 번 훈련해.
#   교체가 일어나면 challenger.pt가 champion.pt가 되고, 다음 실행부터
#   그 새 챔피언을 불러와.
#
# ★ 5일 비교 수정 (2026-11-25) - compare_and_swap에서 날짜별로 먼저 묶음 ★
#   daily_error는 시간마다 1줄씩 저장해서(3498줄), tail(5)를 그대로 쓰면
#   마지막 날 5시간만 보게 돼. 그래서 "확인한 날짜: 1일"이 떴어.
#   이제 날짜별 MAE 평균을 낸 뒤 최근 5일을 가져와서 진짜 5일 평균을 비교해.
#   model_daily_error.csv는 그대로 시간 단위로 저장해.
#
# ============================================================
# 0. 설정 - 여기만 바꾸면 돼
# ============================================================
import json
import os
import shutil
from datetime import date as _date

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# DATA_MODE: "csv"면 merged CSV로 돌리고, "db"면 아래 DB에서 가져와.
# ★ DB로 바꿈 (2026-11-26 집 PC) - tide_observation만 써.
#   weather_observation 테이블은 없어. load_kma.py는 기상을
#   tide_observation에 UPDATE로 채우니까, 기압·풍속·풍향은
#   tide_observation 컬럼에서 직접 가져와.
#   wind_gust_ms·wave_height_m은 tide_observation 컬럼에서 직접 가져와 (ALTER로 추가한 뒤).
#   11개 지역 전부 가져와. 지역마다 따로 윈도우를 만들어서 합쳐.
DATA_MODE = "db"

# CSV 경로 - 여러 위치를 순서대로 찾아봐.
# (DB 모드에서는 CSV가 필요 없어서, 이 찾기는 CSV 모드일 때만 실행돼.)
def find_csv(*candidates):
    for path in candidates:
        if os.path.exists(path):
            print("데이터를 찾았습니다:", path)
            return path
    raise FileNotFoundError(f"데이터를 찾지 못했습니다. 이 경로들을 확인해 주세요: {candidates}")

# ★ 학원 DB 맞춤 - 알려진 값 채움 (2026-11-25)
#   비밀번호는 코드에만 적고, 채팅·GitHub에는 올리지 마.
DB_HOST = "localhost"       # 학원 DB 주소
DB_PORT = 3307              # 학원 MariaDB 포트 (숫자)
DB_USER = "surge"           # 학원 DB 사용자
DB_PASSWORD = "surge"            # ★ 빈칸: .env에 있는 거. 네가 직접 넣어.
DB_NAME = "storm_surge_team"  # 학원 DB 이름

# DB 쿼리 - tide_observation, 11개 지역 전부 (2026-11-26 DB 모드 수정)
#   weather_observation 테이블은 없어. load_kma.py가 기상(기압·풍속·풍향)을
#   tide_observation에 UPDATE로 채워서, 그 컬럼을 직접 읽어.
#   wind_gust_ms·wave_height_m은 tide_observation 컬럼에서 직접 읽어.
#   지역 필터는 없어. 11개 지역 전부 가져와서, 지역마다 따로 윈도우를 만들어.
DB_QUERY = """
SELECT
  station_code,
  obs_time AS timestamp,
  tide_obs_cm,
  tide_pred_cm,
  residual_cm,
  air_pressure_hpa,
  wind_speed_ms,
  wind_gust_ms,
  wind_dir_deg,
  wave_height_m
FROM tide_observation
ORDER BY station_code, obs_time
"""

# X(입력) 컬럼 순서 - train_surge.py랑 똑같아. 순서 바뀌면 결과가 완전히 달라져.
FEATURE_COLS = [
    "tide_obs_cm",
    "residual_cm",
    "air_pressure_hpa",
    "wind_speed_ms",
    "wind_gust_ms",
    "wind_dir_deg",
    "wave_height_m",
]
RESIDUAL_IDX = FEATURE_COLS.index("residual_cm")  # 1번

# 경쟁 규칙
WINDOW = 72                # 지난 72시간을 보고 예측해
TARGET_HOURS = [3, 6, 9, 12, 15, 18, 21, 24]    # 3시간 간격 편차 8개
HIDDEN_SIZE = 64
EPOCHS = 100               # 1시간 데이터는 윈도우가 많아서 100번으로 시작해
COMPETITION_DAYS = 5       # 5일 경쟁
SWAP_THRESHOLD_PCT = 15    # 15% 이상 좋으면 바로 교체, 아니면 최대 15일까지 봐
MAX_DECISION_DAYS = 15     # 교체 여부 결정은 최대 15일 안에
TRAIN_RATIO = 0.8          # 앞 80% 훈련용, 뒤 20% 검사용 (시간 순서대로)

RESULT_DIR = "result"
os.makedirs(RESULT_DIR, exist_ok=True)
REGISTRY_PATH = os.path.join(RESULT_DIR, "model_registry.json")


# ============================================================
# 0-1. registry 읽기 - 교체된 배치 크기를 이어받기 (리뷰 지적 #1 수정)
# ============================================================
# 교체가 일어나면 registry에 새 배치 크기가 저장돼.
# 다음 실행 때 여기서 읽어와서, 교체가 리셋되지 않게 해.
def load_registry_batches():
    # 기본값: 챔피언 32, 챌린저 64
    champ_batch, chall_batch = 32, 64
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, encoding="utf-8") as f:
                reg = json.load(f)
            champ_batch = int(reg.get("champion_batch", 32))
            chall_batch = int(reg.get("challenger_batch", 64))
            print(f"registry에서 배치 크기를 읽었습니다: 챔피언 {champ_batch}, 챌린저 {chall_batch}")
        except Exception as e:
            print(f"registry를 읽지 못했습니다. 기본값(32/64)으로 진행합니다. ({e})")
    return champ_batch, chall_batch


# ============================================================
# 1. 데이터 가져오기 - DB에서 가져오는 게 목표, 지금은 CSV로 먼저 돌려봐
# ============================================================
def load_data():
    if DATA_MODE == "db":
        # DB에서 가져오기 (pymysql 필요: pip install pymysql)
        # ★ DB_QUERY(위쪽 JOIN 쿼리)를 그대로 실행해.
        #   가져온 뒤에는 반드시 이 9개 컬럼이 있어야 해.
        #   timestamp, tide_obs_cm, tide_pred_cm, residual_cm,
        #   air_pressure_hpa, wind_speed_ms, wind_gust_ms, wind_dir_deg, wave_height_m
        #   (테이블의 컬럼 이름이 이 9개와 다르면, DB_QUERY 안의 이름을 DB의 컬럼 이름으로 바꾸고
        #    가져온 뒤에 이 9개 이름으로 바꿔줘야 해.)
        try:
            import pymysql
        except ImportError:
            raise ImportError(
                "pymysql이 필요합니다. 먼저 설치해 주세요: pip install pymysql"
            )
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            charset="utf8mb4",
        )
        try:
            df = pd.read_sql(DB_QUERY, conn)
        finally:
            conn.close()
        print("DB에서 데이터를 가져왔습니다:", DB_NAME, "(tide_observation, 11개 지역)")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        # NULL 채우기 - 기상은 11-22~25만 채워져 있고, 10-25~11-21은 NULL이야.
        # 빈 값(아직 안 들어온 돌풍·파고 등)은 컬럼 평균으로 채우고,
        # 전부 빈 컬럼은 0으로 채워. 안 채우면 훈련할 때 NaN이 돼.
        df[FEATURE_COLS] = df[FEATURE_COLS].fillna(df[FEATURE_COLS].mean()).fillna(0)
    else:
        # CSV에서 가져오기 (지금은 이쪽으로 돌려)
        # 주의: CSV 첫 컬럼은 헤더가 비어 있어 (timestamp가 인덱스로 저장됨). 이름을 붙여줘.
        data_file = find_csv("merged_busan_1yr.csv",
                             "data/merged_busan_1yr.csv",
                             "../merged_busan_1yr.csv",
                             "../data/merged_busan_1yr.csv",
                             "data/merged/merged_busan_1yr.csv")
        df = pd.read_csv(data_file)
        df = df.rename(columns={df.columns[0]: "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["station_code"] = "BUSAN"  # CSV는 부산 1개 지역만 있어.
    df = df.sort_values(["station_code", "timestamp"]).reset_index(drop=True)
    print("가져온 데이터 모양:", df.shape)
    print("기간:", df["timestamp"].iloc[0], "~", df["timestamp"].iloc[-1])
    print(df.head())
    return df


# ============================================================
# 2. 모델 - SurgeLSTM (입력 7개, 출력 2개)
# ============================================================
class SurgeLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=len(FEATURE_COLS), hidden_size=HIDDEN_SIZE,
                            num_layers=1, batch_first=True)
        self.fc = nn.Linear(HIDDEN_SIZE, len(TARGET_HOURS))  # 64개 -> 2개

    def forward(self, x):
        lstm_out, (hidden, cell) = self.lstm(x)
        out = self.fc(hidden[-1])
        return out  # 모양 (개수, 2). [0]=+12h, [1]=+24h


def make_windows(df, feature_cols, mean, std, window=WINDOW, target_hours=TARGET_HOURS):
    # 지난 72시간을 한 묶음으로 잘라서 입력(X)으로 만들고,
    # 각 리드타임(3h, 6h, ... 24h) 편차를 정답(y)으로 만드는 거야.
    # 빈 구간 규칙: 72시간이 1시간씩 안 이어지면 버리고,
    # 목표 시간 중 하나라도 행이 없으면 버려.
    values = df[feature_cols].values.astype(float)
    values_norm = (values - mean) / std
    times = df["timestamp"]
    time_to_idx = {t: i for i, t in enumerate(times)}

    X_list, y_list = [], []
    base_times = []
    target_times_list = [[] for _ in target_hours]  # 리드타임별 목표 시간
    raw_ys_list = [[] for _ in target_hours]        # 리드타임별 실제 편차
    skipped_gap = 0
    skipped_target = 0

    for i in range(len(df) - window - max(target_hours)):
        window_times = times.iloc[i:i + window]
        if window_times.iloc[-1] != window_times.iloc[0] + pd.Timedelta(hours=window - 1):
            skipped_gap += 1
            continue
        end_time = window_times.iloc[-1]
        targets = [end_time + pd.Timedelta(hours=h) for h in target_hours]
        if any(t not in time_to_idx for t in targets):
            skipped_target += 1
            continue
        X_list.append(values_norm[i:i + window])
        y_row = []
        for j, t in enumerate(targets):
            y_row.append(values_norm[time_to_idx[t], RESIDUAL_IDX])
            target_times_list[j].append(t)
            raw_ys_list[j].append(float(df["residual_cm"].iloc[time_to_idx[t]]))
        y_list.append(y_row)
        base_times.append(end_time)

    print(f"윈도우 {len(X_list)}개. 버린 거: 빈 구간 {skipped_gap}개, 목표 시간 없음 {skipped_target}개")
    X = torch.tensor(np.array(X_list), dtype=torch.float32)
    y = torch.tensor(np.array(y_list), dtype=torch.float32)
    raw_ys = [np.array(r) for r in raw_ys_list]
    return X, y, base_times, target_times_list, raw_ys


def make_windows_all(df, feature_cols, mean, std, window=WINDOW, target_hours=TARGET_HOURS):
    # 지역마다 따로 윈도우를 만들어서 합쳐. (합친 모델 방식)
    # 지역을 섞으면 시간이 안 이어져서 윈도우가 깨져. 그래서 지역별로 나눠.
    all_X, all_y = [], []
    all_base = []
    all_target_times = [[] for _ in target_hours]
    all_raw_ys = [[] for _ in target_hours]
    for station, group in df.groupby("station_code", sort=True):
        group = group.sort_values("timestamp").reset_index(drop=True)
        X, y, base, target_times_list, raw_ys = make_windows(
            group, feature_cols, mean, std, window, target_hours)
        if len(X) == 0:
            print(f"  {station}: 윈도우 0개 (데이터가 72시간+{max(target_hours)}시간보다 짧아)")
            continue
        print(f"  {station}: 윈도우 {len(X)}개")
        all_X.append(X)
        all_y.append(y)
        all_base.extend(base)
        for j in range(len(target_hours)):
            all_target_times[j].extend(target_times_list[j])
            all_raw_ys[j].extend(raw_ys[j])
    X = torch.cat(all_X) if all_X else torch.empty(0)
    y = torch.cat(all_y) if all_y else torch.empty(0)
    all_raw_ys = [np.array(r) for r in all_raw_ys]
    return X, y, all_base, all_target_times, all_raw_ys


def train_model(X_train, y_train, batch_size, epochs=EPOCHS):
    # 배치 사이즈만 바꿔서 챔피언이랑 챌린저를 따로 만들어.
    model = SurgeLSTM()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    n = len(X_train)
    step = min(batch_size, n)
    for epoch in range(epochs):
        model.train()
        for start in range(0, n, step):
            xb = X_train[start:start + step]
            yb = y_train[start:start + step]
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
        if (epoch + 1) % 50 == 0:
            print(f"  epoch {epoch + 1}/{epochs}, loss: {loss.item():.4f}")
    return model


def load_champion_model(path):
    # 저장된 챔피언을 불러와. 훈련 안 해. 가중치만 읽어.
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    model = SurgeLSTM()
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model


# ============================================================
# 3. 하루 단위 오차 계산 - 편차 기준, MAE + 진짜 RMSE
# ============================================================
def daily_error(pred_df):
    # 예측 편차랑 실제 편차를 비교해. 하루 1줄씩 저장해.
    # pred_df에 리드타임별 pred_residual_{h}h_cm, actual_residual_{h}h_cm이 들어있어야 해.
    # mae는 모든 리드타임 MAE의 평균이야. 이걸로 챔피언이랑 챌린저를 비교해.
    rows = []
    last_h = TARGET_HOURS[-1]
    for _, row in pred_df.iterrows():
        target = pd.to_datetime(row[f"target_{last_h}h"])
        errs = []
        for h in TARGET_HOURS:
            e = float(row[f"pred_residual_{h}h_cm"]) - float(row[f"actual_residual_{h}h_cm"])
            errs.append(e)
        maes = [abs(e) for e in errs]
        rmses = [(e ** 2) ** 0.5 for e in errs]
        row_out = {
            "date": target.strftime("%Y-%m-%d"),
            "model": row.get("model_version", "champion"),
            "mae": round(sum(maes) / len(maes), 2),
            # RMSE는 제곱해서 평균내고 제곱근을 씌우는 거야. MAE랑은 달라.
            "rmse": round((sum(r ** 2 for r in rmses) / len(rmses)) ** 0.5, 2),
        }
        for j, h in enumerate(TARGET_HOURS):
            row_out[f"mae_{h}h"] = round(maes[j], 2)
            row_out[f"pred_{h}h_cm"] = round(float(row[f"pred_residual_{h}h_cm"]), 2)
            row_out[f"actual_{h}h_cm"] = round(float(row[f"actual_residual_{h}h_cm"]), 2)
        rows.append(row_out)
    if not rows:
        print("오차 계산할 날짜가 없습니다.")
        return pd.DataFrame()
    err_path = os.path.join(RESULT_DIR, "model_daily_error.csv")
    err_df = pd.DataFrame(rows)
    if os.path.exists(err_path):
        old = pd.read_csv(err_path)
        err_df = pd.concat([old, err_df]).drop_duplicates(subset=["date", "model"], keep="last")
    err_df.to_csv(err_path, index=False, encoding="utf-8-sig")
    print("하루 단위 오차 저장이 완료되었습니다:", err_path)
    print(err_df)
    return err_df


# ============================================================
# 4. 챔피언 vs 챌린저 - 5일 경쟁, 15% 규칙
# ============================================================
def compare_and_swap(err_df, champ_batch, chall_batch):
    if err_df.empty:
        print("비교할 오차 기록이 없습니다. 먼저 5일치 오차를 쌓아 주세요.")
        return "대기"
    # 날짜별로 먼저 묶어. (daily_error는 시간마다 1줄씩 저장해서
    #  tail(5)를 그대로 쓰면 마지막 날 5시간만 보게 돼.
    #  날짜별 평균을 내야 진짜 5일 평균이 돼.)
    daily = (err_df.groupby(["date", "model"], as_index=False)["mae"]
             .mean().sort_values("date"))
    # 모델별로 따로 최근 5일을 가져와.
    champ_recent = daily[daily["model"] == "champion"].tail(COMPETITION_DAYS)
    chall_recent = daily[daily["model"] == "challenger"].tail(COMPETITION_DAYS)
    champ = champ_recent["mae"].mean()
    chall = chall_recent["mae"].mean()
    if pd.isna(champ) or pd.isna(chall):
        print("챔피언과 챌린저 오차가 모두 있어야 비교할 수 있습니다.")
        return "대기"
    diff_pct = (champ - chall) / champ * 100 if champ != 0 else 0
    days = len(set(champ_recent["date"]) | set(chall_recent["date"]))
    # 누적 일수: "더 보기"로 5일씩 이어질 때 registry에 쌓아둬. 최대 15일까지.
    old_registry = {}
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, encoding="utf-8") as f:
                old_registry = json.load(f)
        except Exception:
            old_registry = {}
    total_days = int(old_registry.get("days_compared", 0)) + days if old_registry.get("last_decision", "").startswith("더 보기") else days
    print(f"챔피언 5일 평균 MAE: {champ:.2f}cm / 챌린저 5일 평균 MAE: {chall:.2f}cm / 차이: {diff_pct:.1f}% / 확인한 날짜: {days}일 / 누적: {total_days}일")
    if chall < champ and diff_pct >= SWAP_THRESHOLD_PCT:
        decision = "교체 - 챌린저가 챔피언이 됩니다"
        total_days = 0  # 새 경쟁 시작이라 누적 초기화
    elif chall < champ and total_days >= MAX_DECISION_DAYS:
        decision = "유지 - 15일까지 봐도 15% 차이가 나지 않습니다"
        total_days = 0
    elif chall < champ:
        decision = f"더 보기 - 챌린저가 더 좋지만 {diff_pct:.1f}%로 15%에 미치지 못합니다. 5일 더 지켜봅니다"
    else:
        decision = "유지 - 챌린저가 챔피언보다 나쁘거나 같습니다"
        total_days = 0
    print("결정:", decision)
    registry = {"champion_batch": champ_batch, "challenger_batch": chall_batch,
                "last_decision": decision, "diff_pct": round(float(diff_pct), 1),
                "days_compared": int(total_days),
                "champion_mae_5d": round(float(champ), 2),
                "challenger_mae_5d": round(float(chall), 2)}
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print("결정 기록 저장이 완료되었습니다:", REGISTRY_PATH)
    return decision


def swap_champion_and_make_next_challenger(X_train, y_train, mean, std,
                                           champ_batch, chall_batch):
    """교체 결정이 났을 때만 불러. 1) 옛 챔피언 보관 2) 챌린저를 챔피언으로 승격
    3) 새 챌린저 1개 학습 4) registry에 새 배치 크기를 저장해서 다음 날 리셋되지 않게 해."""
    champ_path = os.path.join(RESULT_DIR, "champion.pt")
    chall_path = os.path.join(RESULT_DIR, "challenger.pt")
    today = _date.today().strftime("%Y%m%d")
    archive_path = os.path.join(RESULT_DIR, f"champion_v{today}.pt")
    if os.path.exists(champ_path):
        shutil.copy(champ_path, archive_path)
        print("이전 챔피언 보관이 완료되었습니다:", archive_path)
    shutil.copy(chall_path, champ_path)
    print("챌린저 승격이 완료되었습니다: challenger.pt -> champion.pt")
    # 새 챌린저는 배치만 다르게 (챌린저 배치 x 2). 딱 한 가지만 바꿔.
    # 예: 챌린저가 64였으면 새 챌린저는 128.
    next_chall_batch = chall_batch * 2
    print(f"=== 새 챌린저 훈련 (배치 {next_chall_batch} - 이것만 다릅니다) ===")
    next_challenger = train_model(X_train, y_train, next_chall_batch)
    torch.save({"state_dict": next_challenger.state_dict(), "mean": mean, "std": std,
                "feature_cols": FEATURE_COLS, "window": WINDOW, "target_hours": TARGET_HOURS,
                "batch_size": next_chall_batch},
               chall_path)
    print("새 챌린저 저장이 완료되었습니다:", chall_path)
    # ★ 교체가 다음 날 리셋되지 않게 registry에 새 배치 크기를 저장해.
    # 다음 실행 때 load_registry_batches()가 이걸 읽어와.
    # 새 챔피언 = 옛 챌린저 (배치 chall_batch), 새 챌린저 = next_chall_batch
    registry = {}
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, encoding="utf-8") as f:
                registry = json.load(f)
        except Exception:
            registry = {}
    registry["champion_batch"] = chall_batch
    registry["challenger_batch"] = next_chall_batch
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"registry 배치 크기 업데이트 완료: 챔피언 {chall_batch}, 챌린저 {next_chall_batch}")
    return next_challenger


# ============================================================
# 5. 전체 순서
# ============================================================
def main():
    print("=== 0) registry에서 배치 크기 읽기 (교체 이어받기) ===")
    champ_batch, chall_batch = load_registry_batches()

    print("=== 1) 데이터 가져오기 ===")
    df = load_data()

    print("=== 2) 정규화 (훈련용으로만 평균·표준편차 계산) ===")
    cut_idx = int(len(df) * TRAIN_RATIO)
    cut_time = df["timestamp"].iloc[cut_idx]
    train_df = df.iloc[:cut_idx].copy()
    mean = train_df[FEATURE_COLS].values.astype(float).mean(axis=0)
    std = train_df[FEATURE_COLS].values.astype(float).std(axis=0)
    # ★ std가 0인 컬럼은 0으로 나누면 NaN이 돼.
    #   (예: 아직 값이 안 들어온 기간엔 돌풍·파고가 전부 0으로 채워져서
    #   std가 0이야.) 그런 컬럼은 std를 1로 바꿔. (값이 전부 0이라
    #   정규화해도 0이라서, 훈련에는 영향이 없어.)
    std = np.where(std == 0, 1, std)
    print("평균:", dict(zip(FEATURE_COLS, np.round(mean, 3))))
    print("표준편차:", dict(zip(FEATURE_COLS, np.round(std, 3))))
    print("훈련/검사 기준 시간:", cut_time)

    print(f"=== 3) 윈도우 만들기 (지역마다 따로, 지난 72시간 -> {', '.join(f'+{h}h' for h in TARGET_HOURS)} 편차) ===")
    X, y, base_times, target_times_list, raw_ys = make_windows_all(df, FEATURE_COLS, mean, std)
    # 훈련/검증 나눔은 가장 먼 리드타임(마지막) 기준으로 해.
    last_target_times = target_times_list[-1]
    is_train = np.array([t < cut_time for t in last_target_times])
    X_train, y_train = X[is_train], y[is_train]
    X_test, y_test = X[~is_train], y[~is_train]
    raw_ys_test = [r[~is_train] for r in raw_ys]
    test_base = [t for t, m in zip(base_times, is_train) if not m]
    test_targets = [[t for t, m in zip(times, is_train) if not m] for times in target_times_list]
    print("X 모양:", X.shape, "훈련용:", X_train.shape, "검증용:", X_test.shape)

    print("=== 4) 챔피언 불러오기 (있으면 그대로, 없으면 처음 한 번만 훈련) ===")
    champ_path = os.path.join(RESULT_DIR, "champion.pt")
    champion_trained_now = False
    if os.path.exists(champ_path):
        champion = load_champion_model(champ_path)
        print("저장된 챔피언을 불러왔습니다:", champ_path)
    else:
        print(f"챔피언 파일이 없어 처음 한 번만 훈련합니다 (배치 {champ_batch})")
        champion = train_model(X_train, y_train, champ_batch)
        champion_trained_now = True
    print(f"=== 5) 챌린저 훈련 (배치 {chall_batch} - 이것만 다릅니다) ===")
    challenger = train_model(X_train, y_train, chall_batch)

    print("=== 6) 검증 MAE (cm 단위, 편차 기준) ===")
    champion.eval()
    challenger.eval()
    with torch.no_grad():
        pred_champ = champion(X_test).numpy() * std[RESIDUAL_IDX] + mean[RESIDUAL_IDX]
        pred_chall = challenger(X_test).numpy() * std[RESIDUAL_IDX] + mean[RESIDUAL_IDX]
    mae_champ = []
    mae_chall = []
    for j, h in enumerate(TARGET_HOURS):
        mc = float(np.mean(np.abs(pred_champ[:, j] - raw_ys_test[j])))
        ml = float(np.mean(np.abs(pred_chall[:, j] - raw_ys_test[j])))
        mae_champ.append(mc)
        mae_chall.append(ml)
        print(f"  +{h}h MAE: 챔피언 {mc:.2f}cm / 챌린저 {ml:.2f}cm")
    print(f"챔피언 검증 MAE 평균: {np.mean(mae_champ):.2f}cm / 챌린저 검증 MAE 평균: {np.mean(mae_chall):.2f}cm")

    print("=== 7) 결과 저장 ===")
    # result 폴더가 없으면 torch.save가 실패해. 저장하기 전에 다시 만들어.
    os.makedirs(RESULT_DIR, exist_ok=True)
    # 챔피언은 이번에 새로 훈련한 경우에만 저장해. 불러온 챔피언은 덮지 않아.
    if champion_trained_now:
        torch.save({"state_dict": champion.state_dict(), "mean": mean, "std": std,
                    "feature_cols": FEATURE_COLS, "window": WINDOW, "target_hours": TARGET_HOURS,
                    "batch_size": champ_batch},
                   os.path.join(RESULT_DIR, "champion.pt"))
        print("챔피언 저장이 완료되었습니다: result/champion.pt (처음 훈련이라 새로 저장)")
    else:
        print("챔피언은 불러온 그대로 둡니다. champion.pt를 덮지 않습니다.")
    torch.save({"state_dict": challenger.state_dict(), "mean": mean, "std": std,
                "feature_cols": FEATURE_COLS, "window": WINDOW, "target_hours": TARGET_HOURS,
                "batch_size": chall_batch},
               os.path.join(RESULT_DIR, "challenger.pt"))
    # train_surge.py 결과(surge_prediction.csv)를 덮지 않게 daily는 따로 저장해.
    base_str = [d.strftime("%Y-%m-%d %H:%M") for d in test_base]
    n_test = len(pred_champ)
    pred_data = {
        "base_time": base_str + base_str,
        "model_version": ["champion"] * n_test + ["challenger"] * n_test,
    }
    for j, h in enumerate(TARGET_HOURS):
        dates = [d.strftime("%Y-%m-%d %H:%M") for d in test_targets[j]]
        pred_data[f"target_{h}h"] = dates + dates
        pred_data[f"pred_residual_{h}h_cm"] = np.round(np.concatenate([pred_champ[:, j], pred_chall[:, j]]), 2)
        pred_data[f"actual_residual_{h}h_cm"] = np.round(np.concatenate([raw_ys_test[j], raw_ys_test[j]]), 2)
    pred_df = pd.DataFrame(pred_data)
    pred_df.to_csv(os.path.join(RESULT_DIR, "surge_prediction_daily.csv"), index=False, encoding="utf-8-sig")
    print(pred_df.head())
    print("저장이 완료되었습니다: result/challenger.pt, result/surge_prediction_daily.csv")

    print("=== 8) 하루 단위 오차 계산 ===")
    err_df = daily_error(pred_df)

    print("=== 9) 챔피언 vs 챌린저 비교 ===")
    decision = compare_and_swap(err_df, champ_batch, chall_batch)

    print("=== 10) 실제 교체 & 다음 챌린저 생성 ===")
    # "교체"일 때만 파일을 실제로 바꿔. "더 보기" / "유지" / "대기"면 아무것도 안 바꿔.
    if decision.startswith("교체"):
        swap_champion_and_make_next_challenger(X_train, y_train, mean, std,
                                               champ_batch, chall_batch)
    else:
        print("교체 조건이 아니라서 파일은 그대로 둡니다. 다음 경쟁은 내일 새 데이터가 들어오면 이어서 진행합니다.")
    print("완료되었습니다. 내일 새 데이터가 들어오면 이 파일을 다시 실행해 주세요.")


if __name__ == "__main__":
    main()
