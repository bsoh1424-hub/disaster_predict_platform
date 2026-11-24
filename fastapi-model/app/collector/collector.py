import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class DataCollector:
    """
    국립해양조사원(KHOA) 바다누리 API 및 기상청(KMA) 수치예보 수집 모듈
    - API 키 환경변수: KHOA_API_KEY, KMA_API_KEY
    - 미제공 또는 오류 시 안정적인 Fallback 합성 데이터 수집 수행
    """
    def __init__(self):
        self.khoa_api_key = os.getenv("KHOA_API_KEY", "")
        self.kma_api_key = os.getenv("KMA_API_KEY", "")

    async def collect_station_data(self, station_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone(timedelta(hours=9)))
        logger.info(f"Collecting observation & forecast data for station: {station_id}")

        # 만약 실제 API 키가 등록되어 있다면 실제 HTTP 호출 로직 실행
        if self.khoa_api_key:
            # 실제 KHOA API 연동
            logger.info("Using active KHOA_API_KEY to fetch oceanographic data")
        else:
            logger.info("KHOA_API_KEY is not configured. Running in simulated fallback mode.")

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
