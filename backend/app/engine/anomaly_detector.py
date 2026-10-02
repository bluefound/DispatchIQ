from dataclasses import dataclass
from typing import Any
from app.models.anomaly import AnomalySeverity, AnomalyType


@dataclass
class AnomalyDetectionResult:
    detected: bool
    type: AnomalyType | None
    severity: AnomalySeverity | None
    description: str | None
    details: dict[str, Any] | None


class AnomalyDetector:
    def check_stalled_delivery(
        self, minutes_since_last_update: float, is_delivering: bool
    ) -> AnomalyDetectionResult:
        if is_delivering and minutes_since_last_update > 10.0:
            severity = (
                AnomalySeverity.CRITICAL
                if minutes_since_last_update > 20.0
                else AnomalySeverity.HIGH
            )
            return AnomalyDetectionResult(
                detected=True,
                type=AnomalyType.STALLED_DELIVERY,
                severity=severity,
                description=f"Driver active delivery stalled — no GPS update for {minutes_since_last_update:.1f} minutes",
                details={"minutes_stalled": minutes_since_last_update},
            )
        return AnomalyDetectionResult(detected=False, type=None, severity=None, description=None, details=None)

    def check_eta_miss(
        self, elapsed_minutes: float, estimated_eta_minutes: float
    ) -> AnomalyDetectionResult:
        if elapsed_minutes > (estimated_eta_minutes * 1.8):
            return AnomalyDetectionResult(
                detected=True,
                type=AnomalyType.ETA_MISS,
                severity=AnomalySeverity.MEDIUM,
                description=f"Delivery time ({elapsed_minutes:.1f}m) exceeds 1.8x estimated ETA ({estimated_eta_minutes:.1f}m)",
                details={"elapsed": elapsed_minutes, "estimated": estimated_eta_minutes},
            )
        return AnomalyDetectionResult(detected=False, type=None, severity=None, description=None, details=None)
