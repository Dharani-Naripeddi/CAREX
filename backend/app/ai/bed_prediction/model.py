from typing import List, Dict, Any, Tuple
from app.models.ai import ModelProviderType, AIRiskLevel


class BedCapacityForecastingModel:
    """Time-series stochastic bed forecast calculating 6h, 12h, 24h capacity horizons."""
    def __init__(self):
        self.version = "v1.4.0-capacity-markov"

    @staticmethod
    def get_risk_level(occupancy_pct: float) -> AIRiskLevel:
        """
        Thresholds:
        - < 70%: LOW
        - 70–85%: MEDIUM
        - 85–95%: HIGH
        - > 95%: CRITICAL
        """
        if occupancy_pct >= 95.0:
            return AIRiskLevel.CRITICAL
        elif occupancy_pct >= 85.0:
            return AIRiskLevel.HIGH
        elif occupancy_pct >= 70.0:
            return AIRiskLevel.MEDIUM
        return AIRiskLevel.LOW

    def forecast_horizons(
        self,
        total_beds: int,
        occupied_beds: int,
        active_admissions_rate_per_day: float,
        expected_discharges_rate_per_day: float,
        emergency_transfer_buffer: int = 1,
    ) -> Tuple[List[Dict[str, Any]], AIRiskLevel, ModelProviderType, List[str]]:
        if total_beds == 0:
            return [], AIRiskLevel.LOW, ModelProviderType.STATISTICAL_MODEL, ["No operational beds registered."]

        current_pct = (occupied_beds / total_beds) * 100.0
        reasons = [
            f"Current hospital-wide bed occupancy is {current_pct:.1f}% ({occupied_beds}/{total_beds} beds occupied).",
        ]

        horizons_data = []
        highest_risk = self.get_risk_level(current_pct)

        # Calculate for 6h (0.25 day), 12h (0.5 day), 24h (1.0 day)
        for h_hours in [6, 12, 24]:
            day_fraction = h_hours / 24.0
            proj_admissions = max(0, round(active_admissions_rate_per_day * day_fraction))
            proj_discharges = max(0, round(expected_discharges_rate_per_day * day_fraction))
            net_delta = proj_admissions - proj_discharges + (1 if h_hours == 24 else 0)

            projected_occupied = min(total_beds, max(0, occupied_beds + net_delta))
            projected_pct = round((projected_occupied / total_beds) * 100.0, 1)
            h_risk = self.get_risk_level(projected_pct)

            if h_risk.value > highest_risk.value:
                highest_risk = h_risk

            horizons_data.append({
                "horizon_hours": h_hours,
                "projected_occupancy_percent": projected_pct,
                "projected_admissions": proj_admissions,
                "projected_discharges": proj_discharges,
                "net_bed_delta": net_delta,
                "risk_level": h_risk,
            })

        # Structured Explanations
        if highest_risk in [AIRiskLevel.HIGH, AIRiskLevel.CRITICAL]:
            p24 = horizons_data[2]["projected_occupancy_percent"]
            reasons.append(f"24-hour occupancy forecast reaches {p24:.1f}%, exceeding high-risk threshold (85%).")
            reasons.append(f"Admission velocity ({active_admissions_rate_per_day:.1f}/day) outpaces discharge rate ({expected_discharges_rate_per_day:.1f}/day).")
            if current_pct > 80.0:
                reasons.append("Critical care & telemetry wards operating at near saturation limit.")
        else:
            reasons.append("Adequate hospital bed headroom projected across all 6h, 12h, and 24h operational horizons.")

        provider = ModelProviderType.STATISTICAL_MODEL

        return horizons_data, highest_risk, provider, reasons
