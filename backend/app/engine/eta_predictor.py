import os
import joblib
import pandas as pd


class ETAPredictor:
    def __init__(self, model_path: str = "ml/models/eta_xgb.joblib"):
        self.model = None
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception:
                self.model = None

    def predict(
        self,
        distance_km: float,
        hour_of_day: int,
        day_of_week: int,
        traffic_level: float = 0.5,
        prep_time_minutes: float = 15.0,
        order_size: int = 2,
        driver_rating: float = 4.8,
        driver_total_deliveries: int = 50,
    ) -> float:
        if self.model is None:
            base_travel = (distance_km / 25.0) * 60.0
            return round(prep_time_minutes + base_travel, 1)

        is_peak = 1 if ((hour_of_day >= 12 and hour_of_day <= 14) or (hour_of_day >= 18 and hour_of_day <= 21)) else 0

        input_df = pd.DataFrame(
            [
                {
                    "distance_km": distance_km,
                    "hour_of_day": hour_of_day,
                    "day_of_week": day_of_week,
                    "traffic_level": traffic_level,
                    "prep_time_minutes": prep_time_minutes,
                    "order_size": order_size,
                    "driver_rating": driver_rating,
                    "driver_total_deliveries": driver_total_deliveries,
                    "is_peak_hour": is_peak,
                }
            ]
        )

        pred = self.model.predict(input_df)[0]
        return float(round(pred, 1))
