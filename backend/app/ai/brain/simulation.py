from datetime import datetime
from typing import Dict, List, Any
from app.models.ai import AIRiskLevel
from app.ai.brain.schemas import (
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
    WhatIfSimulationImpact,
    HospitalSystemStatus,
)


class HospitalBrainSimulationEngine:
    """Calculates scenario-based operational 'What-If' projections for hospital capacity planning."""

    @classmethod
    def execute_simulation(
        cls,
        req: WhatIfSimulationRequest,
        baseline_metrics: Dict[str, Any],
    ) -> WhatIfSimulationResponse:
        # Base metrics
        base_bed_occ = float(baseline_metrics.get("bed_occupancy_percent", 72.0))
        base_icu_occ = float(baseline_metrics.get("icu_occupancy_percent", 68.0))
        base_opd_wait = float(baseline_metrics.get("opd_wait_minutes", 25.0))
        base_er_count = float(baseline_metrics.get("active_emergency_count", 4.0))

        # 1. Project Emergency Department Load
        sim_er_count = max(0.0, round(base_er_count * (1.0 + req.emergency_arrival_delta_pct / 100.0), 1))
        er_delta = sim_er_count - base_er_count
        er_risk = AIRiskLevel.CRITICAL if sim_er_count >= 8.0 else AIRiskLevel.HIGH if sim_er_count >= 6.0 else AIRiskLevel.LOW

        # 2. Project Hospital-Wide Bed Occupancy %
        # Inflow increase from ER/OPD adds occupancy; discharge rate change subtracts/adds occupancy
        inflow_impact = (req.emergency_arrival_delta_pct * 0.15) + (req.opd_demand_delta_pct * 0.05)
        discharge_impact = -(req.ward_discharge_rate_delta_pct * 0.20)
        sim_bed_occ = min(100.0, max(10.0, round(base_bed_occ + inflow_impact + discharge_impact, 1)))
        bed_delta = round(sim_bed_occ - base_bed_occ, 1)
        bed_risk = AIRiskLevel.CRITICAL if sim_bed_occ >= 92.0 else AIRiskLevel.HIGH if sim_bed_occ >= 85.0 else AIRiskLevel.MEDIUM if sim_bed_occ >= 75.0 else AIRiskLevel.LOW

        # 3. Project ICU Occupancy %
        sim_icu_occ = min(100.0, max(10.0, round(base_icu_occ + req.icu_occupancy_delta_pct + (req.emergency_arrival_delta_pct * 0.12), 1)))
        icu_delta = round(sim_icu_occ - base_icu_occ, 1)
        icu_risk = AIRiskLevel.CRITICAL if sim_icu_occ >= 90.0 else AIRiskLevel.HIGH if sim_icu_occ >= 80.0 else AIRiskLevel.LOW

        # 4. Project OPD Queue Wait Time (mins)
        # Non-linear queuing delay: higher demand exponentially compounds wait times
        surge_multiplier = 1.0 + (req.opd_demand_delta_pct / 100.0) * 1.4
        sim_opd_wait = max(5.0, round(base_opd_wait * surge_multiplier, 0))
        opd_delta = int(round(sim_opd_wait - base_opd_wait))
        opd_risk = AIRiskLevel.CRITICAL if sim_opd_wait >= 60.0 else AIRiskLevel.HIGH if sim_opd_wait >= 40.0 else AIRiskLevel.LOW

        impacts: Dict[str, WhatIfSimulationImpact] = {
            "hospital_bed_occupancy": WhatIfSimulationImpact(
                baseline_value=base_bed_occ,
                simulated_value=sim_bed_occ,
                delta_value=bed_delta,
                unit="%",
                risk_level=bed_risk,
                impact_description=f"Inpatient bed occupancy shifted by {bed_delta:+.1f}% to {sim_bed_occ:.1f}%",
            ),
            "icu_occupancy": WhatIfSimulationImpact(
                baseline_value=base_icu_occ,
                simulated_value=sim_icu_occ,
                delta_value=icu_delta,
                unit="%",
                risk_level=icu_risk,
                impact_description=f"Critical care ICU capacity projected at {sim_icu_occ:.1f}% ({icu_delta:+.1f}% shift)",
            ),
            "opd_wait_time": WhatIfSimulationImpact(
                baseline_value=base_opd_wait,
                simulated_value=sim_opd_wait,
                delta_value=float(opd_delta),
                unit="mins",
                risk_level=opd_risk,
                impact_description=f"Consultation queue wait time projected at {sim_opd_wait:.0f} mins ({opd_delta:+d} mins delay)",
            ),
            "emergency_arrivals": WhatIfSimulationImpact(
                baseline_value=base_er_count,
                simulated_value=sim_er_count,
                delta_value=round(er_delta, 1),
                unit="active cases",
                risk_level=er_risk,
                impact_description=f"Emergency department active case load projected at {sim_er_count:.1f} cases",
            ),
        }

        # Determine overall projected hospital status
        if sim_bed_occ >= 90.0 or sim_icu_occ >= 92.0 or (sim_bed_occ >= 85.0 and sim_er_count >= 7.0):
            proj_status = HospitalSystemStatus.CRITICAL
        elif sim_bed_occ >= 82.0 or sim_icu_occ >= 82.0 or sim_opd_wait >= 45.0:
            proj_status = HospitalSystemStatus.HIGH_LOAD
        elif sim_bed_occ >= 75.0 or sim_opd_wait >= 30.0:
            proj_status = HospitalSystemStatus.WATCH
        else:
            proj_status = HospitalSystemStatus.STABLE

        affected_depts: List[str] = []
        emerging_risks: List[str] = []
        preemptive_actions: List[str] = []

        if req.emergency_arrival_delta_pct > 0:
            affected_depts.append("Emergency Department")
            emerging_risks.append(f"Emergency arrival surge (+{req.emergency_arrival_delta_pct:.0f}%) may deplete triage bays and resuscitation resources.")
            preemptive_actions.append("Pre-alert on-call emergency physicians and prepare surge holding beds in observation unit.")

        if sim_icu_occ >= 85.0:
            affected_depts.append("Intensive Care Unit (ICU)")
            emerging_risks.append(f"ICU occupancy ({sim_icu_occ:.1f}%) reaches near-saturation threshold; critical care buffer diminished.")
            preemptive_actions.append("Identify stable ICU candidates for early step-down transfer to CCU or telemetry wards.")

        if req.opd_demand_delta_pct > 0:
            affected_depts.append("Outpatient Clinics")
            emerging_risks.append(f"OPD demand increase (+{req.opd_demand_delta_pct:.0f}%) extends consultation waiting times by +{opd_delta} mins.")
            preemptive_actions.append("Stagger token calling times and open overflow consultation rooms.")

        if req.ward_discharge_rate_delta_pct < 0:
            affected_depts.append("Inpatient Wards")
            emerging_risks.append("Slower discharge processing reduces bed turnover rate.")
            preemptive_actions.append("Prioritize pharmacy and billing clearance on pending discharge summaries to accelerate bed release.")

        if not affected_depts:
            affected_depts = ["Hospital-Wide Operations"]
            emerging_risks = ["Operational parameters projected within nominal operating thresholds."]
            preemptive_actions = ["Maintain standard clinical staffing and workflow cadence."]

        title = f"What-If Simulation: ER {req.emergency_arrival_delta_pct:+0.0f}%, ICU {req.icu_occupancy_delta_pct:+0.0f}%, OPD {req.opd_demand_delta_pct:+0.0f}%"

        return WhatIfSimulationResponse(
            scenario_title=title,
            simulation_label="SIMULATION: Scenario-based estimate. Not a real-time forecast.",
            projected_hospital_status=proj_status,
            impacts=impacts,
            affected_departments=affected_depts,
            emerging_risks=emerging_risks,
            recommended_preemptive_actions=preemptive_actions,
            evaluated_at=datetime.utcnow(),
        )
