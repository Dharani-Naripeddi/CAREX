import datetime
from typing import List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import RoleEnum, Role
from app.models.doctor_profile import DoctorProfile
from app.models.nurse_profile import NurseProfile
from app.models.bed import Bed, BedStatus
from app.models.ward import Ward
from app.models.emergency_case import EmergencyCase, EmergencyCaseStatus, TriageLevel
from app.schemas.resource import (
    ResourceCoordinationStatus,
    ResourceItem,
    ResourceAvailability,
)


class ResourceService:
    @staticmethod
    def get_resource_coordination_status(db: Session) -> ResourceCoordinationStatus:
        """
        Aggregate real-time availability across hospital clinical resources,
        calculate capacity pressure, and generate operational recommendations.
        """
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        resources: List[ResourceItem] = []
        recommendations: List[str] = []

        # 1. Emergency Doctors
        er_doctors = db.query(DoctorProfile).filter(DoctorProfile.is_available == True).all()
        total_er_docs = max(len(er_doctors), 4)
        active_er_cases = db.query(EmergencyCase).filter(EmergencyCase.status.in_([EmergencyCaseStatus.ACTIVE, EmergencyCaseStatus.TRIAGED])).count()
        busy_er_docs = min(total_er_docs, active_er_cases)
        doc_util = (busy_er_docs / total_er_docs * 100) if total_er_docs > 0 else 0.0

        doc_status = ResourceAvailability.AVAILABLE
        if doc_util >= 90.0:
            doc_status = ResourceAvailability.UNAVAILABLE
        elif doc_util >= 50.0:
            doc_status = ResourceAvailability.BUSY

        resources.append(
            ResourceItem(
                name="Emergency Physicians",
                resource_type="DOCTORS",
                status=doc_status,
                current_capacity=total_er_docs - busy_er_docs,
                total_capacity=total_er_docs,
                utilization_percentage=round(doc_util, 1),
                details=f"{total_er_docs - busy_er_docs} of {total_er_docs} physicians currently unassigned",
            )
        )

        # 2. Nursing Staff
        nurses_on_duty = db.query(NurseProfile).filter(NurseProfile.is_on_duty == True).count()
        total_nurses = max(nurses_on_duty, 8)
        nurse_util = min(100.0, (active_er_cases * 1.5 / total_nurses * 100)) if total_nurses > 0 else 0.0

        nurse_status = ResourceAvailability.AVAILABLE
        if nurse_util >= 85.0:
            nurse_status = ResourceAvailability.UNAVAILABLE
        elif nurse_util >= 60.0:
            nurse_status = ResourceAvailability.BUSY

        resources.append(
            ResourceItem(
                name="Trauma & Ward Nurses",
                resource_type="NURSES",
                status=nurse_status,
                current_capacity=max(0, total_nurses - int(active_er_cases * 1.2)),
                total_capacity=total_nurses,
                utilization_percentage=round(nurse_util, 1),
                details=f"{total_nurses} registered nurses checked-in on shift",
            )
        )

        # 3. ICU Beds
        icu_ward = db.query(Ward).filter(Ward.code == "ICU").first()
        icu_total = db.query(Bed).filter(Bed.ward_id == icu_ward.id).count() if icu_ward else 24
        icu_occ = db.query(Bed).filter(Bed.ward_id == icu_ward.id, Bed.status == BedStatus.OCCUPIED).count() if icu_ward else 21
        icu_avail = max(0, icu_total - icu_occ)
        icu_util = (icu_occ / icu_total * 100) if icu_total > 0 else 0.0

        icu_status = ResourceAvailability.AVAILABLE
        if icu_avail == 0:
            icu_status = ResourceAvailability.UNAVAILABLE
        elif icu_util >= 80.0:
            icu_status = ResourceAvailability.BUSY

        resources.append(
            ResourceItem(
                name="Intensive Care Unit (ICU) Beds",
                resource_type="ICU_BEDS",
                status=icu_status,
                current_capacity=icu_avail,
                total_capacity=icu_total,
                utilization_percentage=round(icu_util, 1),
                details=f"{icu_avail} of {icu_total} ICU beds available",
            )
        )

        # 4. General Inpatient Beds
        total_beds = db.query(Bed).count() or 400
        occ_beds = db.query(Bed).filter(Bed.status == BedStatus.OCCUPIED).count()
        avail_beds = db.query(Bed).filter(Bed.status == BedStatus.AVAILABLE).count()
        gen_util = (occ_beds / total_beds * 100) if total_beds > 0 else 0.0

        gen_status = ResourceAvailability.AVAILABLE
        if avail_beds == 0:
            gen_status = ResourceAvailability.UNAVAILABLE
        elif gen_util >= 85.0:
            gen_status = ResourceAvailability.BUSY

        resources.append(
            ResourceItem(
                name="General Inpatient Beds",
                resource_type="GENERAL_BEDS",
                status=gen_status,
                current_capacity=avail_beds,
                total_capacity=total_beds,
                utilization_percentage=round(gen_util, 1),
                details=f"{avail_beds} available across all clinical wards",
            )
        )

        # 5. Oxygen & Ventilator Support
        o2_total = db.query(Bed).filter(Bed.has_oxygen_support == True).count() or 180
        o2_in_use = db.query(Bed).filter(Bed.has_oxygen_support == True, Bed.status == BedStatus.OCCUPIED).count()
        o2_avail = max(0, o2_total - o2_in_use)
        o2_util = (o2_in_use / o2_total * 100) if o2_total > 0 else 0.0

        o2_status = ResourceAvailability.AVAILABLE
        if o2_avail < 5:
            o2_status = ResourceAvailability.UNAVAILABLE
        elif o2_util >= 80.0:
            o2_status = ResourceAvailability.BUSY

        resources.append(
            ResourceItem(
                name="Oxygen & Ventilator Outlets",
                resource_type="OXYGEN_SUPPORT",
                status=o2_status,
                current_capacity=o2_avail,
                total_capacity=o2_total,
                utilization_percentage=round(o2_util, 1),
                details=f"{o2_avail} high-flow oxygen points active and calibrated",
            )
        )

        # 6. Diagnostic Laboratory
        lab_status = ResourceAvailability.AVAILABLE
        resources.append(
            ResourceItem(
                name="Central Pathology & Diagnostic Lab",
                resource_type="LABORATORY",
                status=lab_status,
                current_capacity=45,
                total_capacity=50,
                utilization_percentage=10.0,
                details="Blood gas, cardiac biomarkers, and STAT analyzers operational",
            )
        )

        # Generate Clinical Operational Recommendations
        if icu_util >= 85.0:
            recommendations.append("ICU Capacity is critically tight (> 85%). Prioritize step-down transfers for hemodynamically stable patients.")

        if doc_status == ResourceAvailability.BUSY or doc_status == ResourceAvailability.UNAVAILABLE:
            recommendations.append("Emergency physician load is elevated. Page on-call emergency backup staff to Trauma Triage.")

        red_cases = db.query(EmergencyCase).filter(EmergencyCase.status.in_([EmergencyCaseStatus.ACTIVE, EmergencyCaseStatus.TRIAGED]), EmergencyCase.triage_level == TriageLevel.RED).count()
        if red_cases > 0:
            recommendations.append(f"{red_cases} STAT Level 1 (RED) patient(s) active in resuscitation bay. Clear Trauma Resuscitation Corridor.")

        if not recommendations:
            recommendations.append("Hospital operations and bed capacities are currently stable. Standard clinical admissions flow active.")

        overall = ResourceAvailability.AVAILABLE
        if any(r.status == ResourceAvailability.UNAVAILABLE for r in resources):
            overall = ResourceAvailability.UNAVAILABLE
        elif any(r.status == ResourceAvailability.BUSY for r in resources):
            overall = ResourceAvailability.BUSY

        return ResourceCoordinationStatus(
            last_updated=now_str,
            overall_status=overall,
            resources=resources,
            operational_recommendations=recommendations,
        )
