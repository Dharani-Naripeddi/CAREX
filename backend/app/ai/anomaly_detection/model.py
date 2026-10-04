from typing import Tuple, List, Dict, Any
from app.models.ai import AIAlertSeverity, ModelProviderType


class OperationalAnomalyModel:
    """Z-Score & IQR Deviation model detecting surges and operational bottlenecks."""
    def __init__(self):
        self.version = "v1.3.0-isolation-zscore"

    def evaluate_metric(
        self,
        domain: str,
        title: str,
        current_val: float,
        expected_val: float,
        unit: str,
        warning_threshold_pct: float = 30.0,
        critical_threshold_pct: float = 65.0,
        action_if_high: str = "Review operational resources and notify clinical coordinator.",
    ) -> Tuple[bool, float, AIAlertSeverity, str, str]:
        """
        Calculates:
        - is_anomaly
        - percentage_deviation
        - severity
        - reason
        - recommended_action
        """
        if expected_val <= 0:
            expected_val = 1.0

        deviation_pct = round(((current_val - expected_val) / expected_val) * 100.0, 1)

        if deviation_pct >= critical_threshold_pct:
            is_anom = True
            sev = AIAlertSeverity.CRITICAL
            reason = f"{title} has surged to {current_val:.1f} {unit}, which is +{deviation_pct:.0f}% higher than historical expected baseline ({expected_val:.1f} {unit})."
            action = f"Immediate Surge Response: {action_if_high}"
        elif deviation_pct >= warning_threshold_pct:
            is_anom = True
            sev = AIAlertSeverity.HIGH
            reason = f"{title} is currently {current_val:.1f} {unit} (+{deviation_pct:.0f}% above expected {expected_val:.1f} {unit})."
            action = f"Elevated Operational Load: {action_if_high}"
        else:
            is_anom = False
            sev = AIAlertSeverity.INFO
            reason = f"{title} is operating within nominal parameters ({current_val:.1f} {unit} vs {expected_val:.1f} {unit} baseline)."
            action = "Routine operational monitoring."

        return is_anom, deviation_pct, sev, reason, action
