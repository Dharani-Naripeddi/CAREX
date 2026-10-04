from typing import List
from app.models.emergency_case import TriageLevel, ConsciousnessLevel
from app.schemas.emergency import TriageEvaluation


class TriageService:
    @staticmethod
    def evaluate_triage(
        heart_rate: int,
        bp_systolic: int,
        bp_diastolic: int,
        spo2: float,
        temperature: float,
        respiratory_rate: int,
        consciousness: ConsciousnessLevel,
        injury_type: str = "",
        symptoms: str = "",
    ) -> TriageEvaluation:
        """
        Transparent Rule-Based Triage Decision Support System based on Emergency Severity Index (ESI) & Manchester Triage System (MTS).
        Evaluates physiological vitals, consciousness state (AVPU), and traumatic red flags.

        NOTE: Outputs operational prioritization and immediate clinical workflow directives only.
        Does NOT provide medical diagnosis.
        """
        factors: List[str] = []
        is_red = False
        is_orange = False
        is_yellow = False

        # --- LEVEL 1: RED (Resuscitation / Immediate) ---
        if consciousness in [ConsciousnessLevel.UNRESPONSIVE, ConsciousnessLevel.PAIN]:
            factors.append(f"Severely depressed consciousness state ({consciousness.value} on AVPU scale)")
            is_red = True

        if spo2 < 90.0:
            factors.append(f"Severe hypoxia: Critical SpO2 {spo2:.1f}% (< 90%)")
            is_red = True

        if heart_rate > 140 or heart_rate < 40:
            factors.append(f"Critical hemodynamic instability: Heart rate {heart_rate} bpm (extreme tachycardia/bradycardia)")
            is_red = True

        if bp_systolic < 80 or bp_systolic > 220:
            factors.append(f"Severe hypotension or hypertensive crisis: Systolic BP {bp_systolic} mmHg")
            is_red = True

        if respiratory_rate < 8 or respiratory_rate > 35:
            factors.append(f"Imminent respiratory failure: Respiratory rate {respiratory_rate}/min")
            is_red = True

        symptoms_lower = (symptoms or "").lower()
        injury_lower = (injury_type or "").lower()

        red_keywords = ["cardiac arrest", "massive hemorrhage", "severe gunshot", "compound skull", "anaphylaxis", "unresponsive", "severe burns > 40%"]
        for kw in red_keywords:
            if kw in symptoms_lower or kw in injury_lower:
                factors.append(f"High-threat trauma/pathology keyword detected: '{kw}'")
                is_red = True

        if is_red:
            return TriageEvaluation(
                triage_level=TriageLevel.RED,
                contributing_factors=factors,
                recommended_action=(
                    "CRITICAL STAT PRIORITY: Immediate transfer to Trauma Resuscitation Bay 1. "
                    "Activate Trauma Team, notify on-duty Intensivist & Anesthesiologist. "
                    "Initiate high-flow O2, 2 large-bore IV lines, continuous monitor, and prepare crash cart."
                ),
            )

        # --- LEVEL 2: ORANGE (Emergent / Very Urgent - < 10 mins) ---
        if consciousness == ConsciousnessLevel.VOICE:
            factors.append("Altered mental status (Responsive to vocal stimuli only)")
            is_orange = True

        if 90.0 <= spo2 <= 93.0:
            factors.append(f"Compromised oxygenation: SpO2 {spo2:.1f}% (90-93%)")
            is_orange = True

        if (120 <= heart_rate <= 140) or (40 <= heart_rate <= 50):
            factors.append(f"Significant heart rate disturbance: {heart_rate} bpm")
            is_orange = True

        if (80 <= bp_systolic <= 90) or (180 <= bp_systolic <= 220):
            factors.append(f"Borderline perfusion/pressure: Systolic BP {bp_systolic} mmHg")
            is_orange = True

        if 25 <= respiratory_rate <= 35:
            factors.append(f"Tachypnea / respiratory distress: {respiratory_rate} breaths/min")
            is_orange = True

        if temperature >= 39.5:
            factors.append(f"Hyperpyrexia / severe febrile spike: {temperature:.1f}°C (>= 39.5°C)")
            is_orange = True

        orange_keywords = ["chest pain", "substernal", "diaphoresis", "acute stroke", "severe compound fracture", "active bleeding", "stab wound", "severe asthma"]
        for kw in orange_keywords:
            if kw in symptoms_lower or kw in injury_lower:
                factors.append(f"High-acuity clinical indicator: '{kw}'")
                is_orange = True

        if is_orange:
            return TriageEvaluation(
                triage_level=TriageLevel.ORANGE,
                contributing_factors=factors,
                recommended_action=(
                    "VERY URGENT (Priority 2): Place in Acute Emergency Bay within 10 minutes. "
                    "Order 12-lead STAT ECG, cardiac biomarkers, IV access, and continuous vital signs monitoring."
                ),
            )

        # --- LEVEL 3: YELLOW (Urgent - < 30 mins) ---
        if 94.0 <= spo2 <= 95.0:
            factors.append(f"Mildly depressed SpO2: {spo2:.1f}%")
            is_yellow = True

        if 100 <= heart_rate < 120:
            factors.append(f"Moderate tachycardia: {heart_rate} bpm")
            is_yellow = True

        if 140 <= bp_systolic < 180:
            factors.append(f"Elevated systolic BP: {bp_systolic} mmHg")
            is_yellow = True

        if 38.0 <= temperature < 39.5:
            factors.append(f"Febrile elevation: {temperature:.1f}°C")
            is_yellow = True

        if 20 <= respiratory_rate < 25:
            factors.append(f"Mildly elevated respiratory rate: {respiratory_rate}/min")
            is_yellow = True

        yellow_keywords = ["fracture", "moderate laceration", "abdominal pain", "kidney stone", "renal colic", "migraine", "persistent vomiting"]
        for kw in yellow_keywords:
            if kw in symptoms_lower or kw in injury_lower:
                factors.append(f"Moderate severity presentation: '{kw}'")
                is_yellow = True

        if is_yellow:
            if not factors:
                factors.append("Moderate physiological alteration requiring investigation within 30 minutes")
            return TriageEvaluation(
                triage_level=TriageLevel.YELLOW,
                contributing_factors=factors,
                recommended_action=(
                    "URGENT (Priority 3): Assign to Emergency Examination Cubicle. "
                    "Initiate diagnostic workup (blood panel, X-ray/ultrasound as indicated), reassess vitals every 30 mins."
                ),
            )

        # --- LEVEL 4: GREEN (Non-Urgent / Stable) ---
        return TriageEvaluation(
            triage_level=TriageLevel.GREEN,
            contributing_factors=[
                "Physiological vital signs within baseline clinical ranges",
                "Patient alert, conscious, and hemodynamically stable",
            ],
            recommended_action=(
                "STANDARD / NON-URGENT (Priority 4): Route to FastTrack Outpatient clinic or Ambulatory Care. "
                "Standard triage queue with vitals reassessment if waiting exceeds 60 minutes."
            ),
        )
