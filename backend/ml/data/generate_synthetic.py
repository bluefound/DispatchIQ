import numpy as np
import pandas as pd


def generate_eta_dataset(num_samples: int = 5000) -> pd.DataFrame:
    np.random.seed(42)

    distance_km = np.random.uniform(0.5, 20.0, num_samples)
    hour_of_day = np.random.randint(0, 24, num_samples)
    day_of_week = np.random.randint(0, 7, num_samples)
    traffic_level = np.random.uniform(0.1, 1.0, num_samples)
    prep_time_minutes = np.random.uniform(5.0, 35.0, num_samples)
    order_size = np.random.randint(1, 10, num_samples)
    driver_rating = np.random.uniform(3.5, 5.0, num_samples)
    driver_total_deliveries = np.random.randint(5, 500, num_samples)
    is_peak_hour = ((hour_of_day >= 12) & (hour_of_day <= 14)) | (
        (hour_of_day >= 18) & (hour_of_day <= 21)
    )

    base_speed_kmh = 30.0 - (traffic_level * 15.0)
    travel_time_min = (distance_km / base_speed_kmh) * 60.0
    noise = np.random.normal(0, 3.0, num_samples)

    delivery_time_minutes = prep_time_minutes + travel_time_min + (is_peak_hour * 5.0) + noise
    delivery_time_minutes = np.clip(delivery_time_minutes, 10.0, 120.0)

    df = pd.DataFrame(
        {
            "distance_km": distance_km,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "traffic_level": traffic_level,
            "prep_time_minutes": prep_time_minutes,
            "order_size": order_size,
            "driver_rating": driver_rating,
            "driver_total_deliveries": driver_total_deliveries,
            "is_peak_hour": is_peak_hour.astype(int),
            "delivery_time_minutes": delivery_time_minutes,
        }
    )
    return df


if __name__ == "__main__":
    df = generate_eta_dataset()
    df.to_csv("backend/ml/data/synthetic_eta_data.csv", index=False)
    print(f"Generated {len(df)} synthetic ETA records.")
