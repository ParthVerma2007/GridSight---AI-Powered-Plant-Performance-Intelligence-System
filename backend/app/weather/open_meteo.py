import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.models.weather import WeatherRecord
from app.config import settings

logger = logging.getLogger(__name__)

class OpenMeteoClient:
    def __init__(self, db: Session, plant_id: str = "helios-50"):
        self.db = db
        self.plant_id = plant_id
        self.latitude = settings.PLANT_DEFAULT_LATITUDE
        self.longitude = settings.PLANT_DEFAULT_LONGITUDE

    async def fetch_and_cache_weather(
        self,
        start_date: date,
        end_date: date
    ) -> List[WeatherRecord]:
        """
        Fetches solar irradiance and weather metrics from Open-Meteo API.
        Uses historical archive API for past dates, forecast API for future dates.
        Stores records with explicit data_type ('observed' vs 'forecast' vs 'estimated') and provenance.
        Never substitutes current weather for historical observations.
        """
        today = datetime.utcnow().date()
        stored_records: List[WeatherRecord] = []

        # 1. Check if already cached in DB
        cached = self.db.query(WeatherRecord).filter(
            WeatherRecord.plant_id == self.plant_id,
            WeatherRecord.timestamp >= datetime.combine(start_date, datetime.min.time()),
            WeatherRecord.timestamp <= datetime.combine(end_date, datetime.max.time())
        ).all()

        if len(cached) >= ((end_date - start_date).days + 1) * 20:
            # Substantially cached
            return cached

        # 2. Query Open-Meteo
        is_historical = end_date < today
        api_url = settings.OPEN_METEO_BASE_URL if is_historical else settings.OPEN_METEO_FORECAST_URL
        data_type = "observed" if is_historical else "forecast"

        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": "shortwave_radiation_instant,direct_normal_irradiance_instant,diffuse_radiation_instant,temperature_2m,wind_speed_10m,cloud_cover",
            "timezone": "UTC"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    hourly = data.get("hourly", {})
                    times = hourly.get("time", [])
                    ghis = hourly.get("shortwave_radiation_instant", [])
                    dnis = hourly.get("direct_normal_irradiance_instant", [])
                    dhis = hourly.get("diffuse_radiation_instant", [])
                    temps = hourly.get("temperature_2m", [])
                    winds = hourly.get("wind_speed_10m", [])
                    clouds = hourly.get("cloud_cover", [])

                    new_records = []
                    for i, t_str in enumerate(times):
                        dt = datetime.fromisoformat(t_str)
                        # Check duplicate
                        existing = self.db.query(WeatherRecord).filter(
                            WeatherRecord.plant_id == self.plant_id,
                            WeatherRecord.timestamp == dt,
                            WeatherRecord.data_type == data_type
                        ).first()

                        if not existing:
                            ghi_val = ghis[i] if i < len(ghis) else None
                            dni_val = dnis[i] if i < len(dnis) else None
                            dhi_val = dhis[i] if i < len(dhis) else None
                            amb_temp = temps[i] if i < len(temps) else None
                            cell_temp = (amb_temp + (ghi_val / 800.0) * 25.0) if amb_temp and ghi_val else amb_temp
                            w_speed = winds[i] if i < len(winds) else None
                            c_cover = clouds[i] if i < len(clouds) else None

                            rec = WeatherRecord(
                                plant_id=self.plant_id,
                                timestamp=dt,
                                ghi_wm2=ghi_val,
                                dni_wm2=dni_val,
                                dhi_wm2=dhi_val,
                                ambient_temp_c=amb_temp,
                                cell_temp_c=round(cell_temp, 1) if cell_temp else None,
                                wind_speed_ms=w_speed,
                                cloud_cover_pct=c_cover,
                                data_type=data_type,
                                source_provider="open-meteo-api",
                                provenance_notes=f"Retrieved from Open-Meteo {data_type} endpoint (lat={self.latitude}, lon={self.longitude})"
                            )
                            new_records.append(rec)
                            stored_records.append(rec)
                        else:
                            stored_records.append(existing)

                    if new_records:
                        self.db.bulk_save_objects(new_records)
                        self.db.commit()

                    return stored_records

        except Exception as e:
            logger.warning(f"Failed to fetch live weather from Open-Meteo: {str(e)}. Using database cache or synthetic fallback.")

        # If call failed, return whatever we have cached
        return cached
