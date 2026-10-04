from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.bed import Bed, BedStatus
from app.models.ward import Ward
from app.models.room import Room
from app.models.admission import Admission, AdmissionStatus
from app.models.patient import Patient
from app.schemas.bed import (
    BedResponse,
    WardResponse,
    BedDashboardStats,
    BedStatusUpdate,
)
from app.services.audit_service import AuditService


class BedService:
    @staticmethod
    def get_wards(db: Session) -> List[WardResponse]:
        """Fetch all wards with calculated real-time bed occupancy."""
        wards = db.query(Ward).filter(Ward.is_active == True).all()
        results = []

        for w in wards:
            total = db.query(Bed).filter(Bed.ward_id == w.id).count()
            occupied = db.query(Bed).filter(Bed.ward_id == w.id, Bed.status == BedStatus.OCCUPIED).count()
            available = db.query(Bed).filter(Bed.ward_id == w.id, Bed.status == BedStatus.AVAILABLE).count()
            rate = (occupied / total * 100) if total > 0 else 0.0

            results.append(
                WardResponse(
                    id=w.id,
                    name=w.name,
                    code=w.code,
                    description=w.description,
                    floor=w.floor,
                    wing=w.wing,
                    total_beds=total,
                    occupied_beds=occupied,
                    available_beds=available,
                    occupancy_rate=round(rate, 1),
                    is_active=w.is_active,
                )
            )
        return results

    @staticmethod
    def get_beds(
        db: Session,
        ward_id: Optional[int] = None,
        status: Optional[BedStatus] = None,
    ) -> List[BedResponse]:
        """Fetch list of hospital beds with ward and occupant metadata."""
        query = (
            db.query(Bed)
            .options(
                joinedload(Bed.ward),
                joinedload(Bed.room),
                joinedload(Bed.current_admission).joinedload(Admission.patient),
            )
        )

        if ward_id:
            query = query.filter(Bed.ward_id == ward_id)

        if status:
            query = query.filter(Bed.status == status)

        beds = query.order_by(Bed.ward_id.asc(), Bed.bed_number.asc()).all()

        results = []
        for b in beds:
            pat_name = None
            pat_mrn = None
            if b.current_admission and b.current_admission.patient:
                pat_name = b.current_admission.patient.full_name
                pat_mrn = b.current_admission.patient.mrn

            results.append(
                BedResponse(
                    id=b.id,
                    bed_number=b.bed_number,
                    ward_id=b.ward_id,
                    room_id=b.room_id,
                    status=b.status,
                    has_oxygen_support=b.has_oxygen_support,
                    has_ventilator=b.has_ventilator,
                    ward_name=b.ward.name if b.ward else None,
                    room_number=b.room.room_number if b.room else None,
                    current_admission_id=b.current_admission_id,
                    patient_name=pat_name,
                    patient_mrn=pat_mrn,
                    created_at=b.created_at,
                    updated_at=b.updated_at,
                )
            )
        return results

    @staticmethod
    def update_bed_status(
        db: Session,
        bed_id: int,
        status_in: BedStatusUpdate,
        updated_by_id: Optional[int] = None,
    ) -> BedResponse:
        """Update bed operational status (e.g. mark Cleaned -> Available, or Maintenance)."""
        bed = db.query(Bed).options(joinedload(Bed.ward), joinedload(Bed.room)).filter(Bed.id == bed_id).first()
        if not bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bed with ID {bed_id} not found.",
            )

        bed.status = status_in.status
        if status_in.status in [BedStatus.AVAILABLE, BedStatus.CLEANING, BedStatus.MAINTENANCE]:
            if status_in.status == BedStatus.AVAILABLE:
                bed.current_admission_id = None

        db.commit()
        db.refresh(bed)

        AuditService.log(
            db=db,
            action="BED_STATUS_UPDATED",
            entity="BED",
            entity_id=str(bed.id),
            user_id=updated_by_id,
            details={"bed_number": bed.bed_number, "new_status": bed.status.value},
        )

        return BedResponse(
            id=bed.id,
            bed_number=bed.bed_number,
            ward_id=bed.ward_id,
            room_id=bed.room_id,
            status=bed.status,
            has_oxygen_support=bed.has_oxygen_support,
            has_ventilator=bed.has_ventilator,
            ward_name=bed.ward.name if bed.ward else None,
            room_number=bed.room.room_number if bed.room else None,
            current_admission_id=bed.current_admission_id,
            created_at=bed.created_at,
            updated_at=bed.updated_at,
        )

    @staticmethod
    def get_dashboard_stats(db: Session) -> BedDashboardStats:
        """Aggregate high-level Bed telemetry counters and metrics."""
        total = db.query(Bed).count()
        occupied = db.query(Bed).filter(Bed.status == BedStatus.OCCUPIED).count()
        available = db.query(Bed).filter(Bed.status == BedStatus.AVAILABLE).count()
        reserved = db.query(Bed).filter(Bed.status == BedStatus.RESERVED).count()
        maintenance = db.query(Bed).filter(Bed.status == BedStatus.MAINTENANCE).count()
        cleaning = db.query(Bed).filter(Bed.status == BedStatus.CLEANING).count()

        rate = (occupied / total * 100) if total > 0 else 0.0

        # ICU Occupancy
        icu_ward = db.query(Ward).filter(Ward.code == "ICU").first()
        icu_rate = 0.0
        if icu_ward:
            icu_total = db.query(Bed).filter(Bed.ward_id == icu_ward.id).count()
            icu_occ = db.query(Bed).filter(Bed.ward_id == icu_ward.id, Bed.status == BedStatus.OCCUPIED).count()
            icu_rate = (icu_occ / icu_total * 100) if icu_total > 0 else 0.0

        wards = BedService.get_wards(db)

        return BedDashboardStats(
            total_beds=total,
            occupied_beds=occupied,
            available_beds=available,
            reserved_beds=reserved,
            maintenance_beds=maintenance,
            cleaning_beds=cleaning,
            occupancy_rate=round(rate, 1),
            icu_occupancy_rate=round(icu_rate, 1),
            wards=wards,
        )
