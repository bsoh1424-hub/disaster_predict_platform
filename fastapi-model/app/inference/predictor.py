# ============================================================
# predictor_lstm.py — FastAPI용 LSTM 추론 모듈 (main.py 확인 반영본)
# ============================================================
# 지금 predictor.py는 물리 공식으로 예측하고 있어 (.pt를 안 읽어).
# 이 파일이 그걸 LSTM 모델로 바꾸는 교체본이야.
#
# [main.py 확인 완료 — 2026-11-25 11:33]
#   - main.py는 SurgePredictor(MODEL_DIR)를 만들어. MODEL_DIR은
#     models/surge_v1.0.0_2026-11-20/ (폴더). 그래서 __init__은
#     폴더를 받아서 그 안의 surge_model.pt를 읽어.
#   - /predict는 predictor.predict(station_id=..., base_time_str=...,
#     features=...)를 불러. 그래서 predict() 인자는 이 3개야.
#   - 반환은 PredictResponse 모양 그대로: station_id, base_time,
#     model_version, predictions(lead_hour, target_time,
#     residual_cm, exceed_probability).
#   - features dict에는 현재 기압·풍속 몇 개만 들어 있어. 72시간치는
#     없어서, 72시간은 predictor가 DB에서 직접 조회해.
#
# [쓰는 법]
#   1. surge_model.pt를 models/surge_v1.0.0_2026-11-20/ 안에 넣어.
#      (sample_project/result_all/surge_model.pt를 복사해.)
#   2. 이 파일 내용을 app/inference/predictor.py에 통째로 붙여넣기.
#      (클래스 이름 SurgePredictor는 그대로라 main.py는 안 바꿔도 돼.)
#   3. FastAPI 켜는 터미널에서 `pip install torch numpy pymysql` 먼저 해.
#
# [72시간 데이터 — DB에서 조회해]
#   tide_observation + weather_observation JOIN으로 base_time 직전
#   72시간을 가져와. weather_observation이 없거나 값이 NULL이면
#   훈련 평균값으로 채워서 돌려. (기상 데이터가 있으면 더 정확해.)
#   DB에 base_time 직전 72시간치 tide 데이터가 있어야 해.
#   load_khoa.py로 매일 적재해야 72시간이 계속 채워져.
#
# [검증법] 이 파일을 직접 돌리면 test_sample.json으로 정답지 대조를 해.
#   python predictor_lstm.py
# model_output_cm과 똑같이 나오면 입력 준비가 맞는 거야.
# ============================================================

import json
import math
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import torch
import torch.nn as nn

try:
    import pymysql
    HAS_PYMYSQL = True
except Exception:
    pymysql = None
    HAS_PYMYSQL = False


# ------------------------------------------------------------
# base_time 파싱 — 2026-11-26 수정
# ------------------------------------------------------------
# Spring이 보내는 시간이 소수점 7자리야.
#   '2026-11-26T00:32:39.2700522+09:00'
# Python 3.10의 fromisoformat은 소수점 6자리까지만 받아서
# 7자리면 "Invalid isoformat string"으로 500이 나.
# (학원 Python 3.12에서는 됐는데, 집 PC Python 3.10에서는 안 돼.)
# 해결: 소수점을 6자리로 자른 뒤 fromisoformat으로 읽어.
# ------------------------------------------------------------
def _parse_base_time(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)
    return datetime.fromisoformat(s)


# ------------------------------------------------------------
# .env 파일 읽기 (DB 비밀번호 등) — 2026-11-25 12:55 수정
# ------------------------------------------------------------
# 문제: _load_72h_from_db가 DB_PASSWORD를 환경변수에서 읽는데,
# FastAPI를 켠 터미널에는 DB_PASSWORD가 설정된 적이 없어.
# 그래서 DB 연결이 1045로 실패하고 /predict가 500을 냈어.
# 해결: load_khoa.py가 쓰는 .env를 여기서 직접 읽어.
# 찾는 위치: predictor.py가 있는 폴더부터 위로 올라가면서
# (.env가 main_project 루트나 fastapi-model 폴더에 있어도 찾아).
# 이미 환경변수로 설정된 값은 덮어쓰지 않아.
# 여러 .env에 값이 흩어져 있을 수 있어서, 찾은 파일마다 없는 키만 채우고
# 다음 폴더의 .env도 계속 읽는다 (먼저 찾은 값이 이김).
# ------------------------------------------------------------
def _load_env_file():
    here = Path(__file__).resolve().parent
    folders = [here] + list(here.parents) + [Path.cwd()]
    for folder in folders:
        env_path = folder / ".env"
        if not env_path.exists():
            continue
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception:
            pass


_load_env_file()


def _db_config():
    # DB 연결 설정. DB_URL(JDBC)이 있으면 거기서 host/port/database를 읽고,
    # 없거나 파싱이 안 되면 개별 DB_HOST/DB_PORT/DB_NAME을 쓴다.
    # 팀원 PC는 MariaDB 3307, 이 PC는 3306 - 각자 .env의 DB_URL이 정한다.
    # predictor.py 안에 3306을 박아두면 풀 받을 때마다 3307로 되돌아가서 이렇게 바꿈.
    url = os.getenv("DB_URL", "")
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3307"))
    database = os.getenv("DB_NAME", "storm_surge_team")
    if url:
        try:
            rest = url.split("://", 1)[1] if "://" in url else url
            if "/" in rest:
                hostport, database = rest.rsplit("/", 1)
                database = database.split("?", 1)[0] or database
            else:
                hostport = rest
            if hostport.startswith("["):
                # IPv6: [::1]:3306
                host, _, portpart = hostport.partition("]:")
                host = host[1:]
                port = int(portpart) if portpart else port
            elif ":" in hostport:
                host, _, portpart = hostport.partition(":")
                port = int(portpart) if portpart else port
            else:
                host = hostport
        except Exception:
            pass
    return host, port, database

# ------------------------------------------------------------
# 설정
# ------------------------------------------------------------
# test_sample.json 위치 (검증용. 이 파일이 있는 폴더에 같이 둬.
# result_all/test_sample.json을 여기에 복사하면
# `python predictor_lstm.py`로 정답지 대조를 할 수 있어.)
SAMPLE_PATH = Path(__file__).resolve().parent / "test_sample.json"

# 임계값 (DB station_threshold과 같은 값. 주의보 183 / 경보 214)
THRESHOLD_WARN = 183.0
THRESHOLD_ALERT = 214.0

# 버전 표시 (지금 meta.json에 있는 surge v1.0.0 대신 이걸로 보여)
VERSION = "surge_lstm_all_2026-11-25"


# ------------------------------------------------------------
# 모델 구조 — train_surge_all.py의 SurgeLSTM과 똑같아야 해
# LSTM(입력 7개, hidden 64, 1층) + Linear(64 -> 리드타임 개수)
# ------------------------------------------------------------
class SurgeLSTM(nn.Module):
    def __init__(self, input_size=7, hidden_size=64, output_size=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size,
                            num_layers=1, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        lstm_out, (hidden, cell) = self.lstm(x)
        out = self.fc(hidden[-1])
        return out  # 모양 (개수, 리드타임 개수)


# ------------------------------------------------------------
# exceed_probability 계산
# ------------------------------------------------------------
# 예측 수위 = 천문조(tide_pred_cm) + 편차(residual_cm).
# 그게 임계값(183/214)을 넘으면 1.0, 안 넘으면 0.0으로 해.
# ★ 여기는 단순 판정이야. 기존 predictor.py가 쓰던 계산 방식이
# 있으면 이 함수 안만 그걸로 바꿔. 나머지는 그대로 써도 돼.
# ------------------------------------------------------------
def exceed_probability(pred_level_cm, threshold_cm):
    if pred_level_cm is None or threshold_cm is None:
        return None
    return 1.0 if pred_level_cm >= threshold_cm else 0.0


class SurgePredictor:
    """LSTM 모델로 폭풍해일 편차를 예측해.
    .pt 파일은 __init__에서 한 번만 불러. 요청마다 다시 안 읽어."""

    def __init__(self, model_dir):
        # main.py가 모델 폴더를 넘겨줘. 그 안의 surge_model.pt를 읽어.
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "surge_model.pt"
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"surge_model.pt가 없어: {self.model_path} "
                "(sample_project/result_all/surge_model.pt를 models 폴더에 복사해)"
            )
        ckpt = torch.load(self.model_path, map_location="cpu", weights_only=False)
        self.feature_cols = list(ckpt["feature_cols"])  # 7개, 이 순서대로 넣어야 해
        self.window = int(ckpt["window"])               # 72
        self.target_hours = list(ckpt["target_hours"])  # [12, 24]
        self.mean = np.array(ckpt["mean"], dtype=float)
        self.std = np.array(ckpt["std"], dtype=float)
        self.residual_mean = float(ckpt["residual_mean"])
        self.residual_std = float(ckpt["residual_std"])
        self.mae_12h_cm = float(ckpt.get("mae_12h_cm", 0))
        self.mae_24h_cm = float(ckpt.get("mae_24h_cm", 0))
        # main.py의 /health가 predictor.model_version을 읽어.
        self.model_version = VERSION
        self.version = VERSION

        self.model = SurgeLSTM(
            input_size=len(self.feature_cols),
            hidden_size=int(ckpt["hidden_size"]),
            output_size=len(self.target_hours),
        )
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.eval()  # 예측 모드 (훈련 모드가 아님)

    # --------------------------------------------------------
    # 핵심: 72시간 x 7개 (숫자만) -> [+12h 편차, +24h 편차] (cm)
    # --------------------------------------------------------
    def predict_from_raw(self, input_72h_raw):
        """input_72h_raw: 72줄 x 7개, 정규화 안 한 원래 값 (list).
        feature_cols 순서대로 들어와야 해.
        반환: [+12h 편차(cm), +24h 편차(cm)]"""
        x = np.array(input_72h_raw, dtype=float)  # (72, 7)
        if x.shape != (self.window, len(self.feature_cols)):
            raise ValueError(
                f"입력 모양이 틀렸어: {x.shape}, "
                f"기대값: ({self.window}, {len(self.feature_cols)})"
            )
        x_norm = (x - self.mean) / self.std  # 정규화
        x_tensor = torch.tensor(x_norm, dtype=torch.float32).unsqueeze(0)  # (1, 72, 7)
        with torch.no_grad():
            out_norm = self.model(x_tensor).squeeze(0).numpy()  # 정규화된 출력 2개
        # 되돌리기: 출력 * residual_std + residual_mean
        out_cm = out_norm * self.residual_std + self.residual_mean
        return [round(float(v), 2) for v in out_cm]

    # --------------------------------------------------------
    # DB 행 그대로 받아서 예측해
    # --------------------------------------------------------
    # rows: dict 72개. 키는 컬럼 이름 그대로.
    # (예: {"tide_obs_cm": 120.5, "residual_cm": 3.2, ...})
    # feature_cols 순서대로 뽑아서 predict_from_raw()에 넘겨.
    # 컬럼 이름이 달라도 돼. 여기만 DB 컬럼 이름에 맞춰.
    # --------------------------------------------------------
    def predict_from_rows(self, rows):
        if len(rows) != self.window:
            raise ValueError(f"행이 {len(rows)}개야. {self.window}개가 필요해.")
        input_72h_raw = []
        for row in rows:
            input_72h_raw.append([float(row[c]) for c in self.feature_cols])
        return self.predict_from_raw(input_72h_raw)

    # --------------------------------------------------------
    # Spring이 받는 모양으로 만들어
    # --------------------------------------------------------
    # residuals: predict_from_raw() 결과 [+12h, +24h]
    # tide_pred_12h / tide_pred_24h: 그 시간의 천문조(cm).
    #   없으면 exceed_probability는 None으로 나가.
    # 반환: [{"lead_hour": 12, "residual_cm": ..., "exceed_probability": ...},
    #        {"lead_hour": 24, "residual_cm": ..., "exceed_probability": ...}]
    # --------------------------------------------------------
    def to_spring_response(self, residuals, tide_pred_12h=None, tide_pred_24h=None):
        tide_preds = [tide_pred_12h, tide_pred_24h]
        response = []
        for lead_hour, residual, tide_pred in zip(self.target_hours, residuals, tide_preds):
            pred_level = None
            if tide_pred is not None:
                pred_level = float(tide_pred) + float(residual)
            response.append({
                "lead_hour": int(lead_hour),
                "residual_cm": round(float(residual), 2),
                "exceed_probability": exceed_probability(pred_level, THRESHOLD_WARN),
            })
        return response

    # --------------------------------------------------------
    # DB에서 base_time 직전 72시간 x 7개 피처를 가져오기
    # --------------------------------------------------------
    # tide_observation + weather_observation JOIN.
    # weather_observation이 없거나 값이 NULL이면 훈련 평균값으로 채워.
    # 반환: (72, 7) numpy 배열. 데이터가 부족하면 None.
    # --------------------------------------------------------
    def _load_72h_from_db(self, station_id, base_time):
        if not HAS_PYMYSQL:
            raise RuntimeError(
                "pymysql이 안 깔렸어. FastAPI 터미널에서 "
                "`pip install pymysql` 하고 FastAPI를 다시 켜."
            )
        try:
            db_host, db_port, db_name = _db_config()
            conn = pymysql.connect(
                host=db_host,
                port=db_port,
                user=os.getenv("DB_USER", "surge"),
                password=os.getenv("DB_PASSWORD", ""),
                database=db_name,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
        except Exception as e:
            raise RuntimeError(
                f"DB 연결 실패: {e} "
                "(.env의 DB_PASSWORD가 맞는지, MariaDB가 켜져 있는지 확인해)"
            )
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW TABLES LIKE 'weather_observation'")
                has_weather = cur.fetchone() is not None
                end = base_time.strftime("%Y-%m-%d %H:%M:%S")
                start = (base_time - timedelta(hours=self.window)).strftime("%Y-%m-%d %H:%M:%S")
                if has_weather:
                    sql = """SELECT t.obs_time, t.tide_obs_cm, t.residual_cm,
                        COALESCE(w.air_pressure_hpa, t.air_pressure_hpa) AS air_pressure_hpa,
                        COALESCE(w.wind_speed_ms, t.wind_speed_ms) AS wind_speed_ms,
                        w.wind_gust_ms,
                        COALESCE(w.wind_dir_deg, t.wind_dir_deg) AS wind_dir_deg,
                        w.wave_height_m
                        FROM tide_observation t
                        LEFT JOIN weather_observation w
                          ON w.station_code = t.station_code AND w.obs_time = t.obs_time
                        WHERE t.station_code = %s AND t.obs_time > %s AND t.obs_time <= %s
                        ORDER BY t.obs_time ASC"""
                else:
                    sql = """SELECT obs_time, tide_obs_cm, residual_cm, air_pressure_hpa,
                        wind_speed_ms, NULL AS wind_gust_ms, wind_dir_deg,
                        NULL AS wave_height_m
                        FROM tide_observation
                        WHERE station_code = %s AND obs_time > %s AND obs_time <= %s
                        ORDER BY obs_time ASC"""
                cur.execute(sql, (station_id, start, end))
                rows = cur.fetchall()
        finally:
            conn.close()
        if len(rows) < self.window:
            return None
        rows = rows[-self.window:]  # 최근 72행만
        arr = np.full((self.window, len(self.feature_cols)), np.nan, dtype=float)
        for i, r in enumerate(rows):
            for j, col in enumerate(self.feature_cols):
                v = r.get(col)
                if v is not None:
                    arr[i, j] = float(v)
        # NULL → 훈련 평균값으로 채우기 (mean imputation)
        for j in range(arr.shape[1]):
            mask = np.isnan(arr[:, j])
            arr[mask, j] = float(self.mean[j])
        return arr

    # --------------------------------------------------------
    # 초과 확률 (참고용 휴리스틱)
    # --------------------------------------------------------
    # 예전 물리 공식 predictor도 sigmoid로 계산했어.
    # 편차가 클수록 초과 확률↑. sigmoid((편차 - 30) / 10).
    # 편차 30cm → 50%, 60cm → 95%, 0cm → 5%.
    # --------------------------------------------------------
    @staticmethod
    def _exceed_probability(residual_cm):
        try:
            return round(1.0 / (1.0 + math.exp(-(float(residual_cm) - 30.0) / 10.0)), 4)
        except OverflowError:
            return 1.0 if residual_cm > 30 else 0.0

    # --------------------------------------------------------
    # main.py의 /predict가 부르는 부분 — 인자·반환은 main.py 모양 그대로
    # --------------------------------------------------------
    # main.py: predictor.predict(station_id=..., base_time_str=...,
    #         features=...) → 반환을 PredictResponse로 그대로 돌려줘.
    # features dict는 지금 안 써. 72시간은 DB에서 직접 조회해.
    # --------------------------------------------------------
    def predict(self, station_id: str, base_time_str: str,
                features: Optional[Dict[str, Any]] = None):
        base_time = _parse_base_time(base_time_str)
        if base_time.tzinfo is not None:
            base_time = base_time.replace(tzinfo=None)  # DB는 naive DATETIME
        arr = self._load_72h_from_db(station_id, base_time)
        if arr is None:
            raise RuntimeError(
                f"72시간 데이터 부족: station={station_id}, base_time={base_time_str}. "
                "DB에 tide_observation 데이터가 72시간치 있는지 확인해 "
                "(load_khoa.py로 적재해야 해)."
            )
        x_norm = (arr - self.mean) / self.std  # 정규화
        x_tensor = torch.tensor(x_norm, dtype=torch.float32).unsqueeze(0)  # (1, 72, 7)
        with torch.no_grad():
            out_norm = self.model(x_tensor).squeeze(0).numpy()
        out_cm = out_norm * self.residual_std + self.residual_mean  # 되돌리기
        predictions: List[Dict[str, Any]] = []
        for lead, r in zip(self.target_hours, out_cm):
            target = base_time + timedelta(hours=int(lead))
            predictions.append({
                "lead_hour": int(lead),
                "target_time": target.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "residual_cm": round(float(r), 2),
                "exceed_probability": self._exceed_probability(float(r)),
            })
        return {
            "station_id": station_id,
            "base_time": base_time_str,
            "model_version": self.model_version,
            "predictions": predictions,
        }


# ============================================================
# 직접 실행하면 test_sample.json으로 정답지 대조를 해
#   python predictor_lstm.py
# ============================================================
if __name__ == "__main__":
    # 직접 실행하면 test_sample.json으로 정답지 대조를 해.
    # surge_model.pt와 test_sample.json이 있는 폴더를 찾아.
    here = Path(__file__).resolve().parent
    model_dir = here
    for cand in (here, here / "result_all", here / "models"):
        if (cand / "surge_model.pt").exists():
            model_dir = cand
            break
    sample_path = model_dir / "test_sample.json"
    if not sample_path.exists():
        sample_path = SAMPLE_PATH
    predictor = SurgePredictor(model_dir)
    print("모델:", predictor.model_path)
    print("입력 순서:", predictor.feature_cols)
    print("윈도우:", predictor.window)
    print("출력 정의:", predictor.target_hours, "-> [0]=+12h, [1]=+24h")
    print("검증 MAE: +12h", predictor.mae_12h_cm, "cm / +24h", predictor.mae_24h_cm, "cm")

    with open(sample_path, encoding="utf-8") as f:
        sample = json.load(f)

    print("\n--- 정답지 대조 ---")
    print("기준 시간:", sample["base_time"])
    pred = predictor.predict_from_raw(sample["input_72h_raw"])
    print("내 코드 예측:", pred, "cm")
    print("정답지 모델 출력:", sample["model_output_cm"], "cm")
    print("정답지 실제 값:", sample["expected_output_cm"], "cm")
    if pred == sample["model_output_cm"]:
        print("일치해. 입력 준비가 맞아.")
    else:
        print("달라! 입력 순서, 정규화, 모양을 다시 확인해.")
        print("  차이:", [round(a - b, 2) for a, b in zip(pred, sample["model_output_cm"])])


# ============================================================
# main.py 연결 — 확인 완료 (2026-11-25 11:33)
# ============================================================
# main.py가 하는 일 (건드릴 거 없어):
#   MODEL_DIR = models/surge_v1.0.0_2026-11-20/  (폴더)
#   predictor = SurgePredictor(MODEL_DIR)          # 서버 켤 때 한 번만
#   result = predictor.predict(station_id=..., base_time_str=...,
#                              features=...)       # /predict 요청마다
#   → result를 PredictResponse로 그대로 돌려줘.
#
# 이 파일이 하는 일:
#   - __init__에서 MODEL_DIR 안의 surge_model.pt를 읽어.
#   - predict()에서 DB(tide + weather JOIN)로 72시간을 조회해.
#     weather_observation이 없거나 NULL이면 훈련 평균값으로 채워.
#   - LSTM으로 [+12h, +24h 편차]를 내고 PredictResponse 모양으로 돌려줘.
#
# 남은 확인 (학원에서, 순서대로):
#   1. surge_model.pt를 models/surge_v1.0.0_2026-11-20/ 안에 복사했는지.
#   2. FastAPI 켜는 터미널에서 `pip install torch numpy pymysql` 했는지.
#   3. 이 파일을 app/inference/predictor.py로 덮어썼는지.
#   4. FastAPI 재시작 후 /health에서 model_version이
#      surge_lstm_all_2026-11-25로 뜨는지.
#   5. 대시보드에서 /predict가 네 LSTM 값을 내놓는지.
#
# 주의: 지금 DB에는 tide 4일치(2026-11-20~23)만 있어.
# load_khoa.py로 매일 적재해야 72시간이 계속 채워져.
# 기상 데이터는 weather_observation이 생기고 채워져야 들어와.
# 그전까지는 기상 5개가 훈련 평균값으로 채워져서 돌아가.
# ============================================================
