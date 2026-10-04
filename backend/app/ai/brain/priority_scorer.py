from typing import List, Tuple
from app.models.ai import AIAlertSeverity, AIRiskLevel
from app.ai.brain.schemas import OperationalPriorityBreakdown, PriorityFactor


class OperationalPriorityScorer:
    """Calculates an explainable 0 to 100 Operational Priority Score with factor breakdowns.

    Formula:
    Score = Severity_Weight (30%) + Impact_Weight (25%) + Correlation_Weight (25%) + Proximity_Weight (20%)
    """

    @classmethod
    def calculate_score(
        cls,
        severity: AIAlertSeverity,
        risk_level: AIRiskLevel,
        correlated_sources_count: int = 1,
        is_composite: bool = False,
        is_critical_resource: bool = False,
        hours_active: float = 0.5,
    ) -> OperationalPriorityBreakdown:
        factors: List[PriorityFactor] = []

        # 1. Severity Factor (30% weight, max 30 pts)
        sev_map = {
            AIAlertSeverity.CRITICAL: 30.0,
            AIAlertSeverity.HIGH: 22.5,
            AIAlertSeverity.WARNING: 15.0,
            AIAlertSeverity.INFO: 7.5,
        }
        sev_contrib = sev_map.get(severity, 15.0)
        factors.append(
            PriorityFactor(
                name="Alert Severity",
                weight_pct=30.0,
                contribution=round(sev_contrib, 1),
                reason=f"Assigned severity level: {severity.value}",
            )
        )

        # 2. Resource Criticality & Clinical Impact Factor (25% weight, max 25 pts)
        if is_critical_resource or risk_level == AIRiskLevel.CRITICAL:
            impact_contrib = 25.0
            impact_reason = "Impacting critical acute care capacity (e.g. ICU / Resuscitation / Trauma)"
        elif risk_level == AIRiskLevel.HIGH:
            impact_contrib = 18.0
            impact_reason = "Elevated operational strain with high bottleneck potential"
        elif risk_level == AIRiskLevel.MEDIUM:
            impact_contrib = 12.0
            impact_reason = "Moderate departmental load within manageable buffer"
        else:
            impact_contrib = 6.0
            impact_reason = "Standard baseline telemetry deviation"

        factors.append(
            PriorityFactor(
                name="Resource Criticality & Impact",
                weight_pct=25.0,
                contribution=round(impact_contrib, 1),
                reason=impact_reason,
            )
        )

        # 3. Correlation Density Factor (25% weight, max 25 pts)
        if is_composite or correlated_sources_count >= 3:
            corr_contrib = 25.0
            corr_reason = f"Cross-domain composite correlation active ({correlated_sources_count} simultaneous signals)"
        elif correlated_sources_count == 2:
            corr_contrib = 16.0
            corr_reason = "Dual-signal operational cross-correlation detected"
        else:
            corr_contrib = 8.0
            corr_reason = "Single isolated departmental signal"

        factors.append(
            PriorityFactor(
                name="Cross-Module Correlation",
                weight_pct=25.0,
                contribution=round(corr_contrib, 1),
                reason=corr_reason,
            )
        )

        # 4. Proximity & Persistence Factor (20% weight, max 20 pts)
        if hours_active > 3.0:
            persist_contrib = 20.0
            persist_reason = f"Persistent unresolved anomaly ({hours_active:.1f} hours active)"
        elif hours_active > 1.0:
            persist_contrib = 14.0
            persist_reason = f"Ongoing elevated load ({hours_active:.1f} hours active)"
        else:
            persist_contrib = 10.0
            persist_reason = "Recent telemetry trigger (< 1 hour active)"

        factors.append(
            PriorityFactor(
                name="Time Horizon & Persistence",
                weight_pct=20.0,
                contribution=round(persist_contrib, 1),
                reason=persist_reason,
            )
        )

        total_score = int(round(sum(f.contribution for f in factors)))
        total_score = max(5, min(100, total_score))

        if total_score >= 80:
            rating = "CRITICAL"
            summary = "Immediate executive and operational review recommended. Multiple high-acuity capacity bottlenecks."
        elif total_score >= 60:
            rating = "HIGH"
            summary = "Substantial operational strain detected across department workflows."
        elif total_score >= 40:
            rating = "MODERATE"
            summary = "Noticeable load increase requiring proactive monitoring and load balancing."
        else:
            rating = "LOW"
            summary = "Nominal system operation with minor statistical variations."

        return OperationalPriorityBreakdown(
            score=total_score,
            rating=rating,
            factors=factors,
            summary_explanation=summary,
        )
