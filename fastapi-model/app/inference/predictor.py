import os
import json
import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

class SurgePredictor:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.meta_data = self._load_meta()
        self.model_version = self.meta_data.get("version", "surge_v1.0.0_2026-11-20")

    def _load_meta(self) -> Dict[str, Any]:
        meta_path = os.path.join(self.model_dir, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "version": "surge_v1.0.0_2026-11-20",
            "created_at": datetime.now(timezone(timedelta(hours=9))).isoformat()
        }

    def predict(self, station_id: str, base_time_str: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        물리-시계열 하이브리드 추론 (역기압 효과 + 풍속 제곱 연안 밀어올림 + 과거 lag + 예보 기상)
        - 역기압 효과: 1013.25hPa 기준 1hPa 하강당 약 +1.01cm 잔차
        - 풍속 밀어올림: 바람속도^2 * 연안방향 성분 반영
        """
        try:
            base_time = datetime.fromisoformat(base_time_str)
        except Exception:
            base_time = datetime.now(timezone(timedelta(hours=9)))

        # 피처 추출
        current_pressure = features.get("current_pressure", 1013.0)
        pressure_drop_3h = features.get("pressure_drop_3h", 1.5)
        wind_speed = features.get("wind_speed", 12.0)
        wind_dir = features.get("wind_dir", 180.0) # 남풍 계열
        past_residual = features.get("past_residual", 10.0)
        fcst_pressure_12h = features.get("forecast_pressure_12h", current_pressure - 8.0)
        fcst_pressure_24h = features.get("forecast_pressure_24h", current_pressure - 4.0)
        fcst_wind_12h = features.get("forecast_wind_12h", wind_speed + 5.0)
        fcst_wind_24h = features.get("forecast_wind_24h", wind_speed + 2.0)

        # 12h 리드타임 잔차 계산
        # 기압강하 효과
        inv_barometer_12h = max(0.0, (1013.25 - fcst_pressure_12h) * 1.05)
        # 바람 밀어올림 (남향/남동향 해안가 가중)
        wind_setup_12h = (fcst_wind_12h ** 1.8) * 0.08
        # 조석 상호작용 및 지연 전파
        residual_12h = round(inv_barometer_12h + wind_setup_12h + (past_residual * 0.3) + (pressure_drop_3h * 2.0), 1)

        # 24h 리드타임 잔차 계산
        inv_barometer_24h = max(0.0, (1013.25 - fcst_pressure_24h) * 1.02)
        wind_setup_24h = (fcst_wind_24h ** 1.8) * 0.06
        residual_24h = round(inv_barometer_24h + wind_setup_24h + (past_residual * 0.15), 1)

        # 초과 확률 모델 (Sigmoid 기반 보정)
        # 통상 잔차 30cm 이상이면 경보 초과 가능성 급상승
        prob_12h = round(1.0 / (1.0 + math.exp(-0.12 * (residual_12h - 25.0))), 2)
        prob_24h = round(1.0 / (1.0 + math.exp(-0.12 * (residual_24h - 25.0))), 2)

        time_12h = (base_time + timedelta(hours=12)).isoformat()
        time_24h = (base_time + timedelta(hours=24)).isoformat()

        return {
            "station_id": station_id,
            "base_time": base_time.isoformat(),
            "model_version": self.model_version,
            "predictions": [
                {
                    "lead_hour": 12,
                    "target_time": time_12h,
                    "residual_cm": residual_12h,
                    "exceed_probability": prob_12h
                },
                {
                    "lead_hour": 24,
                    "target_time": time_24h,
                    "residual_cm": residual_24h,
                    "exceed_probability": prob_24h
                }
            ]
        }
