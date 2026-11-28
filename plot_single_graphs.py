# plot_single_graphs.py — surge_prediction.csv로 하나로 그린 그래프 2개 만들기
# 훈련을 다시 안 해도 돼. 이미 나온 CSV만 있으면 돼.
#
# 쓰는 법 (CSV가 있는 폴더에서):
#   python plot_single_graphs.py
#   python plot_single_graphs.py result_all_3_24/surge_prediction.csv 부산
#
# 입력: surge_prediction.csv — region, base_time, target_3h, pred_residual_3h_cm, actual_residual_3h_cm, ... (3h부터 24h까지 8개)
# 출력: 2개
#   1) single_date_overlay.png — 가로축 날짜, 선 8개 (+3h~+24h 예측선) + 실제 선 1개, 한 판에 겹쳐 그리기, 부산만, 최근 5일만
#   2) single_leadtime_curve.png — 가로축 예측 시간(3, 6, 9, 12, 15, 18, 21, 24), 세로축 편차, 가장 최근 base_time 1개의 예측 곡선 1개 + 실제 곡선 1개
#
# 주의: 1번은 선이 8개라 겹쳐서 보기 어려울 수 있어. 2번이 예보 곡선으로 보기는 더 깔끔해.
# 지역을 바꾸려면 부산 대신 인천, 울산 같은 지역 이름을 넣어. 다시 훈련 안 해도 돼.

import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

TARGET_HOURS = [3, 6, 9, 12, 15, 18, 21, 24]
CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "result_all_3_24/surge_prediction.csv"
REGION = sys.argv[2] if len(sys.argv) > 2 else "부산"

# 8개 시간 색. 파랑 계열부터 주황 계열까지 순서대로.
COLORS = ["#2563eb", "#0891b2", "#059669", "#65a30d", "#ca8a04", "#ea580c", "#dc2626", "#7c3aed"]

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["base_time"] = pd.to_datetime(df["base_time"])
df = df[df["region"] == REGION].sort_values("base_time").reset_index(drop=True)
if len(df) == 0:
    print(f"지역 {REGION} 데이터가 없어. CSV의 region 값을 확인해.")
    raise SystemExit(1)

last_base = df["base_time"].max()
graph_start = last_base - pd.Timedelta(days=5)
df5 = df[df["base_time"] >= graph_start].reset_index(drop=True)
print(f"그래프 범위: {REGION} {graph_start} ~ {last_base} ({len(df5)}개)")

# 시간별 MAE (최근 5일, 이 지역만)
mae_by_hour = {}
for h in TARGET_HOURS:
    mae_by_hour[h] = float(np.mean(np.abs(df5[f"pred_residual_{h}h_cm"] - df5[f"actual_residual_{h}h_cm"])))
mae_mean = float(np.mean(list(mae_by_hour.values())))
print(f"최근 5일 평균 MAE: {mae_mean:.2f}cm")
for h in TARGET_HOURS:
    print(f"  +{h}h {mae_by_hour[h]:.2f}cm")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["figure.facecolor"] = "white"

# ------------------------------------------------------------
# 1) 날짜가 가로축, 선 8개 한 판에 겹치기
# ------------------------------------------------------------
# 실제 선은 +12h 실제값을 대표로 1개만 그려. 시간마다 실제값은 거의 같은 계열이라 8개를 다 그리면 겹쳐서 안 보여.
# 예측선은 시간마다 1개씩, 6시간 이동평균으로 진하게 그려.
fig1, ax1 = plt.subplots(figsize=(12, 5))
actual_times = pd.to_datetime(df5["target_12h"])
actual_s = pd.Series(df5["actual_residual_12h_cm"].values, index=actual_times)
actual_smooth = actual_s.rolling(6, min_periods=1).mean()
ax1.plot(actual_times, actual_s, color="#111827", linewidth=0.8, alpha=0.25)
ax1.plot(actual_times, actual_smooth, color="#111827", linewidth=2.2, label="실제 편차")
for j, h in enumerate(TARGET_HOURS):
    times = pd.to_datetime(df5[f"target_{h}h"])
    pred_s = pd.Series(df5[f"pred_residual_{h}h_cm"].values, index=times)
    pred_smooth = pred_s.rolling(6, min_periods=1).mean()
    ax1.plot(times, pred_smooth, color=COLORS[j], linewidth=1.6,
             label=f"+{h}h 예측 (MAE {mae_by_hour[h]:.2f}cm)")
ax1.set_title(f"{REGION} 편차 예측 최근 5일 — 날짜 축, 선 8개 한 판에 (평균 MAE {mae_mean:.2f}cm)", fontsize=13)
ax1.set_xlabel("날짜", fontsize=11)
ax1.set_ylabel("편차 (cm)", fontsize=11)
ax1.grid(True, color="#e5e7eb", linewidth=0.6)
ax1.set_axisbelow(True)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)
ax1.legend(frameon=False, fontsize=9, loc="upper left", ncol=3)
fig1.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig("single_date_overlay.png", dpi=200)
print("저장 완료: single_date_overlay.png")
plt.close(fig1)

# ------------------------------------------------------------
# 2) 예측 시간이 가로축, 가장 최근 base_time 1개의 곡선 1개
# ------------------------------------------------------------
# 가장 최근 base_time 1행만 골라. 가로축은 3, 6, 9, 12, 15, 18, 21, 24, 세로축은 그 시간의 편차야.
latest = df.iloc[-1]
latest_base = latest["base_time"]
pred_curve = [float(latest[f"pred_residual_{h}h_cm"]) for h in TARGET_HOURS]
actual_curve = [float(latest[f"actual_residual_{h}h_cm"]) for h in TARGET_HOURS]
row_mae = float(np.mean(np.abs(np.array(pred_curve) - np.array(actual_curve))))
print(f"예보 곡선 기준 시간: {latest_base} (이 행의 MAE {row_mae:.2f}cm)")

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.plot(TARGET_HOURS, actual_curve, color="#2563eb", linewidth=2.2, marker="o", markersize=6, label="실제 편차")
ax2.plot(TARGET_HOURS, pred_curve, color="#f97316", linewidth=2.2, marker="o", markersize=6, label="예측 편차")
ax2.set_xticks(TARGET_HOURS)
ax2.set_xticklabels([f"+{h}h" for h in TARGET_HOURS])
ax2.set_title(f"{REGION} 편차 예보 곡선 — 기준 {latest_base.strftime('%Y-%m-%d %H:%M')} (이 행 MAE {row_mae:.2f}cm)", fontsize=13)
ax2.set_xlabel("예측 시간", fontsize=11)
ax2.set_ylabel("편차 (cm)", fontsize=11)
ax2.grid(True, color="#e5e7eb", linewidth=0.6)
ax2.set_axisbelow(True)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
ax2.legend(frameon=False, fontsize=10, loc="best")
# 점마다 값도 적어. 읽을 때 편해.
for x, y in zip(TARGET_HOURS, pred_curve):
    ax2.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8, color="#ea580c")
plt.tight_layout()
plt.savefig("single_leadtime_curve.png", dpi=200)
print("저장 완료: single_leadtime_curve.png")
plt.close(fig2)
print("완료되었습니다.")
