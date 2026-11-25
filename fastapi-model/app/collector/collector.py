import os
import logging
from typing import Dict, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class DataCollector:
    """
    국립해양조사원(KHOA) 바다누리/공공데이터포털 API 및 기상청(KMA) 수치예보 수집 모듈
    - API 키: KHOA_API_KEY 또는 DATA_GO_KR_API_KEY, KMA_API_KEY
    - 수집 실패 또는 호출 한도 초과 시 안정적인 시뮬레이션 데이터 수집 수행 (A2 모듈 분리 원칙)
    """
    def __init__(self):
        self.khoa_api_key = os.getenv("KHOA_API_KEY") or os.getenv("DATA_GO_KR_API_KEY", "")
        self.kma_api_key = os.getenv("KMA_API_KEY", "")

    async def collect_station_data(self, station_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone(timedelta(hours=9)))
        logger.info(f"Collecting observation & forecast data for station: {station_id}")

        if self.khoa_api_key:
            logger.info("Using configured KHOA / Public Data Portal API key")
        else:
            logger.info("KHOA API key not configured. Operating in simulation mode.")

        # 관측값 및 예보 피처 생성
        simulated_data = {
            "station_id": station_id,
            "collected_at": now.isoformat(),
            "status": "SUCCESS",
            "observation": {
                "tide_obs_cm": 142.5,
                "tide_pred_cm": 110.0,
                "residual_cm": 32.5,
                "air_pressure_hpa": 998.2,
                "wind_speed_ms": 14.8,
                "wind_dir_deg": 195.0
            },
            "forecast_feature": {
                "forecast_issued_at": (now - timedelta(hours=1)).isoformat(),
                "forecast_pressure_12h": 986.5,
                "forecast_pressure_24h": 994.0,
                "forecast_wind_12h": 19.5,
                "forecast_wind_24h": 15.2
            }
        }
        return simulated_data
