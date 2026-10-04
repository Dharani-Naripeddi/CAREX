from typing import List, Dict, Any, Tuple
from app.models.emergency_case import TriageLevel, ConsciousnessLevel
from app.models.ai import AIRiskLevel, ModelProviderType


class TriageRulesEngine:
    """Deterministic Emergency Severity Index (ESI) & Manchester Triage physiological decision support."""
    def __init__(self):
        self.version = "v1.5.0-esi-guidelines"

    def evaluate(
        self,
        age: int,
        symptoms: str,
        heart_rate: int | None,
        bp_systolic: int | None,
        bp_diastolic: int | None,
        spo2: float | None,
        temperature: float | None,
        respiratory_rate: int | None,
        consciousness: ConsciousnessLevel,
    ) -> Tuple[TriageLevel, AIRiskLevel, List[str], List[Dict[str, Any]], str, int]:
        """
        Evaluates triage priority, contributing factors, and operational target assessment window.
        """
        factors: List[str] = []
        flags: List[Dict[str, Any]] = []
        level = TriageLevel.GREEN
        target_mins = 120
        sym_lower = (symptoms or "").lower()

        # 1. Critical RED triggers (Immediate Resuscitation)
        if consciousness == ConsciousnessLevel.UNRESPONSIVE:
            level = TriageLevel.RED
            factors.append("Unresponsive consciousness level (GCS < 8 equivalent)")
            flags.append({"param": "Consciousness", "value": "UNRESPONSIVE", "status": "CRITICAL"})
        
        if spo2 is not None and spo2 < 90.0:
            level = TriageLevel.RED
            factors.append(f"Severe hypoxia (SpO2 {spo2}% < 90%)")
            flags.append({"param": "SpO2", "value": f"{spo2}%", "status": "CRITICAL"})

        if bp_systolic is not None and bp_systolic < 80:
            level = TriageLevel.RED
            factors.append(f"Severe decompensated shock (Systolic BP {bp_systolic} mmHg < 80)")
            flags.append({"param": "BP Systolic", "value": f"{bp_systolic} mmHg", "status": "CRITICAL"})

        if heart_rate is not None and (heart_rate > 150 or heart_rate < 40):
            level = TriageLevel.RED
            factors.append(f"Life-threatening arrhythmia/rate (HR {heart_rate} bpm)")
            flags.append({"param": "Heart Rate", "value": f"{heart_rate} bpm", "status": "CRITICAL"})

        if any(w in sym_lower for w in ["cardiac arrest", "massive hemorrhage", "anaphylaxis", "severe stemi", "gunshot to chest", "cyanosis"]):
            level = TriageLevel.RED
            factors.append("Severe high-acuity life-threat keywords identified")

        if level == TriageLevel.RED:
            return (
                TriageLevel.RED,
                AIRiskLevel.CRITICAL,
                factors,
                flags,
                "Immediate Resuscitation Bay mobilization. Direct attending emergency physician and trauma resuscitation team.",
                0,
            )

        # 2. Emergent ORANGE triggers (Very Urgent - Target < 10 mins)
        if consciousness in [ConsciousnessLevel.PAIN, ConsciousnessLevel.VERBAL]:
            level = TriageLevel.ORANGE
            factors.append(f"Altered mental status / responsiveness ({consciousness.value})")
            flags.append({"param": "Consciousness", "value": consciousness.value, "status": "WARNING"})

        if spo2 is not None and 90.0 <= spo2 <= 94.0:
            level = TriageLevel.ORANGE
            factors.append(f"Compromised oxygenation (SpO2 {spo2}%)")
            flags.append({"param": "SpO2", "value": f"{spo2}%", "status": "WARNING"})

        if bp_systolic is not None and (bp_systolic < 90 or bp_systolic > 200):
            level = TriageLevel.ORANGE
            factors.append(f"Significant hemodynamic compromise (BP Systolic {bp_systolic} mmHg)")
            flags.append({"param": "BP Systolic", "value": f"{bp_systolic} mmHg", "status": "WARNING"})

        if heart_rate is not None and (heart_rate > 125 or heart_rate < 50):
            level = TriageLevel.ORANGE
            factors.append(f"Significant tachycardia/bradycardia (HR {heart_rate} bpm)")
            flags.append({"param": "Heart Rate", "value": f"{heart_rate} bpm", "status": "WARNING"})

        if respiratory_rate is not None and (respiratory_rate > 30 or respiratory_rate < 10):
            level = TriageLevel.ORANGE
            factors.append(f"Severe tachypnea / bradypnea (RR {respiratory_rate} breaths/min)")
            flags.append({"param": "Respiratory Rate", "value": f"{respiratory_rate} /min", "status": "WARNING"})

        if any(w in sym_lower for w in ["crushing chest pain", "stroke", "paralysis", "hemiplegia", "severe dyspnea", "major burn"]):
            level = TriageLevel.ORANGE
            factors.append("High-risk clinical presentation keywords detected")

        if level == TriageLevel.ORANGE:
            return (
                TriageLevel.ORANGE,
                AIRiskLevel.HIGH,
                factors,
                flags,
                "Urgent Acute Care Bay. Continuous cardiac & pulse oximetry monitoring. Physician evaluation within 10 minutes.",
                10,
            )

        # 3. Urgent YELLOW triggers (Urgent - Target < 60 mins)
        if temperature is not None and (temperature > 39.0 or temperature < 35.5):
            level = TriageLevel.YELLOW
            factors.append(f"Severe pyrexia / hypothermia (Temp {temperature}°C)")
            flags.append({"param": "Temperature", "value": f"{temperature}°C", "status": "INFO"})

        if heart_rate is not None and (100 < heart_rate <= 125):
            level = TriageLevel.YELLOW
            factors.append(f"Mild-moderate tachycardia (HR {heart_rate} bpm)")
            flags.append({"param": "Heart Rate", "value": f"{heart_rate} bpm", "status": "INFO"})

        if any(w in sym_lower for w in ["moderate abdominal pain", "fracture", "deep laceration", "uncontrolled vomiting", "asthma flare"]):
            level = TriageLevel.YELLOW
            factors.append("Urgent acute symptom presentation requiring diagnostic workup")

        if level == TriageLevel.YELLOW:
            return (
                TriageLevel.YELLOW,
                AIRiskLevel.MEDIUM,
                factors,
                flags,
                "Priority assessment bay. Establish IV access, order routine diagnostic blood work, nurse vital recheck every 30 mins.",
                60,
            )

        # 4. Standard Non-Urgent GREEN triggers (Target < 120 mins)
        if not factors:
            factors.append("Physiological vital signs within stable baseline thresholds")
        
        return (
            TriageLevel.GREEN,
            AIRiskLevel.LOW,
            factors,
            flags,
            "Standard Outpatient / Minor Injury treatment area. Routine triage observation.",
            120,
        )
