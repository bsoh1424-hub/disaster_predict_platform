# ============================================================
# [변경 기록 - 2026-11-27]
# - 원본: train_surge_all.py (TARGET_HOURS=[12, 24], 출력 2개)
# - 변경: TARGET_HOURS=[3, 6, 9, 12, 15, 18, 21, 24], 출력 8개
# - 이유: 리액트 그래프를 3시간 단위로 그리고 싶어서.
#         옛날 모델은 출력이 2개라서 3, 6, 9시간을 못 내.
#         출력 개수가 바뀌면 마지막 층(Linear 64->2)이 64->8로 바뀌고,
#         정답(y)도 +3h~+24h 편차 8개로 바뀌어서 다시 훈련해야 해.
# - 주의: 이 파일은 원본 result_all/을 덮지 않아.
#         결과는 result_all_3_24/ 폴더에 따로 저장돼.
#         지금 FastAPI가 쓰고 있는 surge_lstm_all_2026-11-25 모델은 그대로 둬.
#         이 새 모델을 FastAPI에 넣으려면 predictor.py도 출력 8개로 바꿔야 해.
#         predictor.py는 팀원 파트야. 바꾸기 전에 팀원한테 먼저 말해.
# ============================================================
# train_surge_all_3_24.py — 폭풍해일 잔차 예측 LSTM, 11개 지역 합쳐서 1개 모델
# LSTM.html STEP 3 기준: "필요하면 나머지 10개 파일을 같은 컬럼으로 concat해서 확장합니다. 모델 구조는 그대로예요."
# 스펙 문장 그대로: "모델을 11개 만들 필요 없어요. LSTM 1개"로 간다.
#
# 합치는 방법 (중요 — 날짜로 묶는 게 아님):
#   11개 지역이 같은 기간을 커버하니까, 날짜로 묶으면 한 시간에 값이 11개가 돼서 모양이 안 맞아.
#   그래서 지역별로 윈도우를 따로 만들고, 그 윈도우들을 모아서 한 번에 훈련해.
#   윈도우 하나는 여전히 한 지역의 72시간이야. 섞인 윈도우는 없어.
#   모델은 지역을 구분 못 해. 11개 지역 데이터를 다 보고 평균적인 패턴을 배우는 거야.
#
# 데이터: merged_*_1yr.csv 11개 전부. 같은 폴더에 있어야 해.
#   (C:\project\10곳 부이 + 조위\ 안에 있는 10개를 sample_project로 복사해 와.)
#   부산 8,750행 + 나머지 10개 = 총 약 91,048행. 윈도우는 약 9만 개.
#   훈련 시간: 부산 1개가 2~3분 걸렸으니, 11개 합치면 20~30분 정도 걸려.
#
# 출력: result_all_3_24/ 폴더에 (result_all이랑 안 겹치게)
#   surge_model.pt — 11개 지역으로 훈련한 모델 1개 + 스케일러 + 입력 순서 + 출력 정의
#   surge_prediction.csv — 검사용 예측 + 실제 편차 + 지역 컬럼 (지역별 MAE도 볼 수 있어)
#   test_sample.json — 테스트 샘플 1개 (연결 후 대조용)
#   prediction.png — 검사용 실제 vs 예측 그래프
#
# 실행: CSV 11개가 있는 폴더에서 python train_surge_all_3_24.py

import json
import os

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import matplotlib.pyplot as plt

# ============================================================
# STEP 0. 설정 — 11개 지역 파일
# ============================================================
# 지역 이름 -> 파일명. 파일 11개가 이 스크립트랑 같은 폴더에 있어야 해.
DATA_FILES = {
    "부산": "merged_busan_1yr.csv",
    "인천": "merged_incheon_1yr.csv",
    "덕적도": "merged_deokjeokdo_1yr.csv",
    "추자도": "merged_chujado_1yr.csv",
    "서귀포": "merged_seogwipo_1yr.csv",
    "울릉도": "merged_ulleungdo_1yr.csv",
    "통영": "merged_tongyeong_1yr.csv",
    "거문도": "merged_geomundo_1yr.csv",
    "울산": "merged_ulsan_1yr.csv",
    "포항": "merged_pohang_1yr.csv",
    "거제도": "merged_geoje_1yr.csv",
}

# X(입력) 컬럼 순서 — 이 순서가 곧 predict() 입력 순서야. 절대 바꾸지 마.
# train_surge.py(부산 1개)랑 똑같은 순서야.
FEATURE_COLS = [
    "tide_obs_cm",       # 실측조위 (cm)
    "residual_cm",       # 편차 (cm) — t이기도 해
    "air_pressure_hpa",  # 현지기압 (hPa)
    "wind_speed_ms",     # 풍속 (m/s)
    "wind_gust_ms",      # 순간풍속 / 돌풍 (m/s)
    "wind_dir_deg",      # 풍향 (도, 0=북 90=동 180=남 270=서)
    "wave_height_m",     # 유의파고 (m 단위 — 주의)
]
RESIDUAL_IDX = FEATURE_COLS.index("residual_cm")  # 1번. y를 되돌릴 때 써.

WINDOW = 72              # 지난 72시간(3일)을 보고 예측해
TARGET_HOURS = [3, 6, 9, 12, 15, 18, 21, 24]  # 3시간 단위로 +3h부터 +24h까지 편차 8개를 한 번에 예측해
HIDDEN_SIZE = 64         # 부산 모델이랑 똑같이 64
EPOCHS = 100             # 데이터가 10배라 한 번 돌리는 데 20~30분 걸려. 느리면 50으로 줄여도 돼.
BATCH_SIZE = 32          # 한 번에 32개씩 학습해
TRAIN_RATIO = 0.8        # 앞 80%는 훈련용, 뒤 20%는 검사용 (시간 순서대로, 지역마다 따로)

RESULT_DIR = "result_all_3_24"  # result_all이랑 안 겹치게 따로. 옛날 12/24h 모델을 덮지 않아.
os.makedirs(RESULT_DIR, exist_ok=True)


# ============================================================
# STEP 1. 파일 11개 읽기
# ============================================================
# 주의: CSV 첫 컬럼은 헤더가 비어 있어 (timestamp가 인덱스로 저장됨). 이름을 붙여줘.
dfs = {}
for region, fname in DATA_FILES.items():
    df = pd.read_csv(fname)
    df = df.rename(columns={df.columns[0]: "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    dfs[region] = df
    print(f"{region}: {df.shape}, {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")

total_rows = sum(len(df) for df in dfs.values())
print("총 행수 (11개 지역 합계):", total_rows)


# ============================================================
# STEP 2. 훈련용 / 검사용 나누는 기준 시간 (지역마다 따로, 시간 순서대로)
# ============================================================
# 각 지역마다 앞 80% 지점의 시간을 기준으로 잘라.
# 2026-10-18 폭풍(인천 127.7cm, 덕적도 90.8cm)은 뒤 20%에 들어가서 검사용이 돼.
cut_times = {}
for region, df in dfs.items():
    cut_idx = int(len(df) * TRAIN_RATIO)
    cut_times[region] = df["timestamp"].iloc[cut_idx]
    print(f"{region} 훈련/검사 기준 시간: {cut_times[region]}")


# ============================================================
# STEP 3. 정규화 기준 (11개 지역 훈련용을 다 합쳐서 평균·표준편차 계산)
# ============================================================
# 평균이랑 표준편차는 11개 지역 훈련용 80% 구간을 다 합쳐서 계산해.
# 검사용 숫자를 미리 보면 안 되니까, 훈련용으로만 계산하는 건 부산 때랑 똑같아.
train_parts = []
for region, df in dfs.items():
    cut_idx = int(len(df) * TRAIN_RATIO)
    train_parts.append(df.iloc[:cut_idx][FEATURE_COLS].values.astype(float))
train_values = np.concatenate(train_parts, axis=0)
mean = train_values.mean(axis=0)
std = train_values.std(axis=0)
print("11개 지역 훈련용 합계 행수:", train_values.shape)
print("평균:", dict(zip(FEATURE_COLS, np.round(mean, 3))))
print("표준편차:", dict(zip(FEATURE_COLS, np.round(std, 3))))


# ============================================================
# STEP 4. 윈도우 만들기 — 지역별로 따로 만들고, 그다음 합쳐
# ============================================================
# 윈도우: 지난 72시간(72줄)을 한 묶음으로 잘라서 입력(X)으로 만들고,
#   그 뒤 3시간 / 6시간 / 9시간 / 12시간 / 15시간 / 18시간 / 21시간 / 24시간 뒤 편차를 정답(y)으로 만드는 거야.
# 빈 구간 규칙: 72시간 안에 시간이 1시간씩 안 이어지면 그 윈도우는 버려.
#   목표 시간 자리에 행이 없으면 그 윈도우도 버려.
# 합치는 법: 지역별로 윈도우를 만들고, 윈도우들을 모으는 거야.
#   윈도우 하나는 한 지역의 72시간이야. 지역이 섞인 윈도우는 절대 없어.
def make_windows(df, feature_cols, mean, std, window=WINDOW, target_hours=TARGET_HOURS):
    values = df[feature_cols].values.astype(float)
    values_norm = (values - mean) / std
    times = df["timestamp"]
    # timestamp -> 행 번호. 목표 시간 자리를 빨리 찾기 위한 거야.
    time_to_idx = {t: i for i, t in enumerate(times)}

    X_list, y_list = [], []
    base_times = []
    target_times_all = []  # 윈도우마다 목표 시간 8개씩 들어 있어. [ [ +3h, +6h, ..., +24h ], ... ]
    raw_y_list = []  # 정규화 안 한 실제 편차 8개 (나중에 MAE를 cm로 잴 때 써)
    skipped_gap = 0   # 빈 구간 때문에 버린 윈도우 수
    skipped_target = 0  # 목표 시간 행이 없어서 버린 윈도우 수

    for i in range(len(df) - window - max(target_hours)):
        # 1) 72시간이 1시간씩 이어지는지 확인해. 안 이어지면 버려.
        window_times = times.iloc[i:i + window]
        # 1시간 간격이면 첫 시간 + 71시간이 마지막 시간과 같아야 해.
        if window_times.iloc[-1] != window_times.iloc[0] + pd.Timedelta(hours=window - 1):
            skipped_gap += 1
            continue
        # 2) 목표 시간 8개 자리에 행이 있는지 확인해.
        end_time = window_times.iloc[-1]
        targets = [end_time + pd.Timedelta(hours=h) for h in target_hours]
        if any(t not in time_to_idx for t in targets):
            skipped_target += 1
            continue
        # 3) 입력(X) = 지난 72시간 7개 피처, 정답(y) = 목표 시간 8개 편차
        X_list.append(values_norm[i:i + window])
        y_list.append([values_norm[time_to_idx[t], RESIDUAL_IDX] for t in targets])
        base_times.append(end_time)
        target_times_all.append(targets)
        raw_y_list.append([float(df["residual_cm"].iloc[time_to_idx[t]]) for t in targets])

    print(f"  윈도우 {len(X_list)}개. 버린 거: 빈 구간 {skipped_gap}개, 목표 시간 없음 {skipped_target}개")
    X = torch.tensor(np.array(X_list), dtype=torch.float32)
    y = torch.tensor(np.array(y_list), dtype=torch.float32)
    return X, y, base_times, target_times_all, np.array(raw_y_list)


# 지역별로 윈도우를 만들고, 훈련용/검사용으로 나눈 뒤 한데 모아.
X_train_list, y_train_list = [], []
X_test_list, y_test_list = [], []
raw_y_train_list, raw_y_test_list = [], []
test_base = []
test_target_times = []  # 검사용 윈도우마다 목표 시간 8개씩
test_region = []  # 검사용 윈도우가 어느 지역인지 기록해. 지역별 MAE를 잴 때 써.
for region, df in dfs.items():
    print(f"[{region}] 윈도우 만드는 중...")
    X, y, base_times, target_times_all, raw_y = make_windows(df, FEATURE_COLS, mean, std)
    # 훈련용 / 검사용 나누기 — 마지막 목표 시간(+24h)이 기준 시간보다 앞이면 훈련용, 뒤면 검사용
    is_train = np.array([t[-1] < cut_times[region] for t in target_times_all])
    X_train_list.append(X[is_train])
    y_train_list.append(y[is_train])
    X_test_list.append(X[~is_train])
    y_test_list.append(y[~is_train])
    raw_y_train_list.append(raw_y[is_train])
    raw_y_test_list.append(raw_y[~is_train])
    test_base.extend([t for t, m in zip(base_times, is_train) if not m])
    test_target_times.extend([t for t, m in zip(target_times_all, is_train) if not m])
    test_region.extend([region] * int((~is_train).sum()))

X_train = torch.cat(X_train_list, dim=0)
y_train = torch.cat(y_train_list, dim=0)
X_test = torch.cat(X_test_list, dim=0)
y_test = torch.cat(y_test_list, dim=0)
raw_y_test = np.concatenate(raw_y_test_list)  # 모양 (검사용 개수, 8). 열 순서 = TARGET_HOURS 순서
test_region = np.array(test_region)
print("훈련용 X:", X_train.shape, "검사용 X:", X_test.shape)
print("검사용 지역별 개수:", {r: int((test_region == r).sum()) for r in DATA_FILES})


# ============================================================
# STEP 5. 모델 만들기 — nn.LSTM + nn.Linear (출력 8개). 부산 모델이랑 구조는 똑같고 출력만 8개야.
# ============================================================
class SurgeLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=len(FEATURE_COLS), hidden_size=HIDDEN_SIZE,
                            num_layers=1, batch_first=True)
        self.fc = nn.Linear(HIDDEN_SIZE, len(TARGET_HOURS))  # 64개 -> 8개

    def forward(self, x):
        lstm_out, (hidden, cell) = self.lstm(x)
        out = self.fc(hidden[-1])
        return out  # 모양 (개수, 8). [0]=+3h, [1]=+6h, [2]=+9h, [3]=+12h, [4]=+15h, [5]=+18h, [6]=+21h, [7]=+24h


model = SurgeLSTM()
print(model)

# ============================================================
# STEP 6. 훈련
# ============================================================
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

n_train = len(X_train)
for epoch in range(EPOCHS):
    model.train()
    epoch_loss = 0.0
    for start in range(0, n_train, BATCH_SIZE):
        xb = X_train[start:start + BATCH_SIZE]
        yb = y_train[start:start + BATCH_SIZE]
        optimizer.zero_grad()
        pred = model(xb)
        loss = criterion(pred, yb)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item() * len(xb)
    epoch_loss /= n_train
    if (epoch + 1) % 10 == 0:
        print(f"epoch {epoch + 1}/{EPOCHS}, loss: {epoch_loss:.4f}")

# ============================================================
# STEP 7. 검증 — 안 쓴 뒤 20%로 예측 vs 실제 비교하기 (전체 + 지역별)
# ============================================================
model.eval()
with torch.no_grad():
    pred_test_norm = model(X_test)

pred_test = pred_test_norm.numpy() * std[RESIDUAL_IDX] + mean[RESIDUAL_IDX]  # 모양 (검사용 개수, 8)
mae_by_hour = {}
for j, h in enumerate(TARGET_HOURS):
    mae_by_hour[h] = float(np.mean(np.abs(pred_test[:, j] - raw_y_test[:, j])))
mae_mean = float(np.mean(list(mae_by_hour.values())))
print(f"검증 MAE (11개 지역 전체, 8개 시간 평균): {mae_mean:.2f}cm")
for h in TARGET_HOURS:
    print(f"  +{h}h {mae_by_hour[h]:.2f}cm")
print(f"검사용 편차 범위: 실제 {raw_y_test.min():.1f}~{raw_y_test.max():.1f}cm")

# 지역별 MAE — 합친 모델이 어느 지역에서 잘 맞고 어디서 안 맞는지 보는 거야.
# 인천처럼 편차가 큰 지역에서 MAE가 크게 나오면, 그 지역은 따로 모델을 만드는 걸 고려해봐.
print("--- 지역별 검증 MAE ---")
region_mae = {}
for region in DATA_FILES:
    mask = test_region == region
    if mask.sum() == 0:
        continue
    region_mae[region] = [float(np.mean(np.abs(pred_test[mask, j] - raw_y_test[mask, j]))) for j in range(len(TARGET_HOURS))]
    mae_str = " / ".join([f"+{h}h {region_mae[region][j]:.2f}cm" for j, h in enumerate(TARGET_HOURS)])
    print(f"{region}: {mae_str} (검사용 {int(mask.sum())}개)")
print("부산 단독 모델 MAE (비교용, 12/24h만): +12h 4.41cm / +24h 4.48cm")

# ============================================================
# STEP 8. 결과 저장하기 — result_all_3_24/ 폴더에
# ============================================================
# 1) surge_prediction.csv: 검사용 예측 + 실제 편차 + 지역 표. 리액트 그래프는 이 파일로 그리면 돼.
result_dict = {
    "region": test_region,
    "base_time": [t.strftime("%Y-%m-%d %H:%M") for t in test_base],
}
for j, h in enumerate(TARGET_HOURS):
    result_dict[f"target_{h}h"] = [t[j].strftime("%Y-%m-%d %H:%M") for t in test_target_times]
    result_dict[f"pred_residual_{h}h_cm"] = np.round(pred_test[:, j], 2)
    result_dict[f"actual_residual_{h}h_cm"] = np.round(raw_y_test[:, j], 2)
result = pd.DataFrame(result_dict)
result.to_csv(os.path.join(RESULT_DIR, "surge_prediction.csv"), index=False, encoding="utf-8-sig")
print("저장 완료:", os.path.join(RESULT_DIR, "surge_prediction.csv"))

# 2) surge_model.pt: 훈련된 모델 1개 + 스케일러 + 입력 순서 + 출력 정의 + 지역 목록
torch.save({
    "state_dict": model.state_dict(),
    "feature_cols": FEATURE_COLS,
    "window": WINDOW,
    "target_hours": TARGET_HOURS,
    "mean": mean, "std": std,
    "residual_mean": float(mean[RESIDUAL_IDX]),
    "residual_std": float(std[RESIDUAL_IDX]),
    "hidden_size": HIDDEN_SIZE,
    "mae_by_hour_cm": {h: round(v, 2) for h, v in mae_by_hour.items()},
    "mae_mean_cm": round(mae_mean, 2),
    "mae_12h_cm": round(mae_by_hour[12], 2),
    "mae_24h_cm": round(mae_by_hour[24], 2),
    "regions": list(DATA_FILES.keys()),  # 11개 지역 전부로 훈련한 모델이라는 표시
    "region_mae_cm": {r: [round(v, 2) for v in vals] for r, vals in region_mae.items()},
}, os.path.join(RESULT_DIR, "surge_model.pt"))
print("저장 완료:", os.path.join(RESULT_DIR, "surge_model.pt"))

# 3) test_sample.json: 테스트 샘플 1개 (검사용 첫 번째 윈도우). 연결 후 대조용이야.
# 첫 검사용 윈도우가 어느 지역인지 확인하고, 그 지역 파일에서 원본 72시간을 가져와.
sample_idx = 0
sample_region = test_region[sample_idx]
sample_df = dfs[sample_region]
sample_raw = sample_df[FEATURE_COLS].values.astype(float)
first_base = test_base[sample_idx]
start_row = int(sample_df.index[sample_df["timestamp"] == first_base].tolist()[0]) - (WINDOW - 1)
sample_input = sample_raw[start_row:start_row + WINDOW].tolist()
sample_target_times = test_target_times[sample_idx]
test_sample = {
    "region": sample_region,
    "feature_cols": FEATURE_COLS,
    "window": WINDOW,
    "base_time": first_base.strftime("%Y-%m-%d %H:%M"),
    "target_hours": TARGET_HOURS,
    "target_times": [t.strftime("%Y-%m-%d %H:%M") for t in sample_target_times],
    "target_12h": sample_target_times[TARGET_HOURS.index(12)].strftime("%Y-%m-%d %H:%M"),
    "target_24h": sample_target_times[TARGET_HOURS.index(24)].strftime("%Y-%m-%d %H:%M"),
    "input_72h_raw": sample_input,
    "expected_output_cm": [round(float(v), 2) for v in raw_y_test[sample_idx]],
    "model_output_cm": [round(float(v), 2) for v in pred_test[sample_idx]],
}
with open(os.path.join(RESULT_DIR, "test_sample.json"), "w", encoding="utf-8") as f:
    json.dump(test_sample, f, ensure_ascii=False, indent=2)
print("저장 완료:", os.path.join(RESULT_DIR, "test_sample.json"), f"(지역: {sample_region})")

# 4) prediction.png: 검사용 실제 편차 vs 예측 편차 그래프 (3h부터 24h까지 8개, 최근 5일, 부산만)
# 그래프는 검사용 전체(약 70일)가 아니라 최근 5일만 그려.
# 기준은 base_time(윈도우 끝 시간) 마지막 날부터 5일 전이야. MAE랑 CSV는 전체 검사용 그대로야.
# 지역을 섞으면 시간축이 겹쳐서 지저분해져. 그래서 그래프는 부산만 그려.
# 예쁘게 그리는 법: 1시간 원본은 옅게, 6시간 이동평균은 진하게 그려. 선이 덜 울퉁불퉁해 보여.
GRAPH_REGION = "부산"
last_base = max([t for t, r in zip(test_base, test_region) if r == GRAPH_REGION])
graph_start = last_base - pd.Timedelta(days=5)
graph_mask = np.array([(t >= graph_start) and (r == GRAPH_REGION) for t, r in zip(test_base, test_region)])
graph_target_times = [t for t, m in zip(test_target_times, graph_mask) if m]
graph_raw = raw_y_test[graph_mask]
graph_pred = pred_test[graph_mask]
print(f"그래프 범위: {GRAPH_REGION} {graph_start} ~ {last_base} ({int(graph_mask.sum())}개)")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["figure.facecolor"] = "white"
fig, axes = plt.subplots(4, 2, figsize=(12, 8), sharex=True, sharey=True)
axes = axes.ravel()
for j, h in enumerate(TARGET_HOURS):
    ax = axes[j]
    target_times_j = pd.to_datetime([t[j] for t in graph_target_times])
    raw_s = pd.Series(graph_raw[:, j], index=target_times_j)
    pred_s = pd.Series(graph_pred[:, j], index=target_times_j)
    raw_smooth = raw_s.rolling(6, min_periods=1).mean()
    pred_smooth = pred_s.rolling(6, min_periods=1).mean()
    ax.plot(target_times_j, raw_s, color="#2563eb", linewidth=0.8, alpha=0.35)
    ax.plot(target_times_j, raw_smooth, color="#2563eb", linewidth=1.8, label="실제 편차")
    ax.plot(target_times_j, pred_s, color="#f97316", linewidth=0.8, alpha=0.35)
    ax.plot(target_times_j, pred_smooth, color="#f97316", linewidth=1.8, label="예측 편차")
    ax.set_title(f"+{h}h  (MAE {mae_by_hour[h]:.2f}cm)", fontsize=11)
    ax.set_ylabel("편차 (cm)", fontsize=10)
    ax.grid(True, color="#e5e7eb", linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    if j == 0:
        ax.legend(frameon=False, fontsize=9, loc="upper left")
fig.suptitle(f"부산 편차 예측 최근 5일 3~24h (평균 MAE {mae_mean:.2f}cm)", fontsize=14)
for ax in axes[6:]:
    ax.set_xlabel("날짜", fontsize=10)
fig.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, "prediction.png"), dpi=200)
print("저장 완료:", os.path.join(RESULT_DIR, "prediction.png"))

print("완료되었습니다.")
print("다음: 지역별 MAE를 봐. 어느 지역이 유독 안 좋으면 그 지역은 따로 모델을 만드는 걸 쌤이랑 얘기해봐.")
print("  부산 단독 모델 MAE (비교용, 12/24h만): +12h 4.41cm / +24h 4.48cm")
print("  주의: 이 모델을 FastAPI에 넣으려면 predictor.py도 출력 8개로 바꿔야 해. predictor.py는 팀원 파트야.")
