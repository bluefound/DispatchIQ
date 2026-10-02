import os
import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from ml.data.generate_synthetic import generate_eta_dataset


def train():
    df = generate_eta_dataset(num_samples=10000)

    features = [
        "distance_km",
        "hour_of_day",
        "day_of_week",
        "traffic_level",
        "prep_time_minutes",
        "order_size",
        "driver_rating",
        "driver_total_deliveries",
        "is_peak_hour",
    ]
    target = "delivery_time_minutes"

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators=100,
        learning_rate=0.08,
        max_depth=5,
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"Model Training Complete!")
    print(f"MAE: {mae:.2f} minutes")
    print(f"R2 Score: {r2:.4f}")

    os.makedirs("backend/ml/models", exist_ok=True)
    model_path = "backend/ml/models/eta_xgb.joblib"
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")


if __name__ == "__main__":
    train()
