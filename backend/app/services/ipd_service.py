import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from fastapi import HTTPException, status
from app.models.admission import Admission, AdmissionStatus, DischargeCondition
from app.models.bed import Bed, BedStatus
from app.models.ward import Ward
from app.models.bed_transfer import BedTransfer
from app.models.patient import Patient
from app.models.user import User
from app.models.emergency_case import EmergencyCase, EmergencyCaseStatus
from app.schemas.ipd import (
    AdmissionCreate,
    AdmissionResponse,
    BedTransferCreate,
    BedTransferResponse,
    DischargeRequest,
)
from app.services.audit_service import AuditService


class IpdService:
    @staticmethod
    def generate_admission_number(db: Session) -> str:
        """Generate unique sequential admission number format: ADM-YYYY-XXXX."""
        current_year = datetime.date.today().year
        prefix = f"ADM-{current_year}-"

        latest = (
            db.query(Admission)
            .filter(Admission.admission_number.like(f"{prefix}%"))
            .order_by(desc(Admission.id))
            .first()
        )

        if latest and latest.admission_number.startswith(prefix):
            try:
                seq = int(latest.admission_number.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:04d}"

    @staticmethod
    def create_admission(
        db: Session,
        adm_in: AdmissionCreate,
        created_by_id: Optional[int] = None,
    ) -> AdmissionResponse:
        """Admit patient to Inpatient Ward and allocate Bed."""
        patient = db.query(Patient).filter(Patient.id == adm_in.patient_id).first()
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {adm_in.patient_id} not found.")

        doctor = db.query(User).filter(User.id == adm_in.admitting_doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor {adm_in.admitting_doctor_id} not found.")

        ward = db.query(Ward).filter(Ward.id == adm_in.ward_id).first()
        if not ward:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ward {adm_in.ward_id} not found.")

        bed = db.query(Bed).filter(Bed.id == adm_in.bed_id).first()
        if not bed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bed {adm_in.bed_id} not found.")

        if bed.status == BedStatus.OCCUPIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bed {bed.bed_number} is currently occupied by another patient.",
            )

        adm_num = IpdService.generate_admission_number(db)
        admission_time = datetime.datetime.now(datetime.timezone.utc)

        admission = Admission(
            admission_number=adm_num,
            patient_id=adm_in.patient_id,
            admitting_doctor_id=adm_in.admitting_doctor_id,
            ward_id=adm_in.ward_id,
            bed_id=adm_in.bed_id,
            admission_date=admission_time,
            admission_reason=adm_in.admission_reason,
            expected_stay_days=adm_in.expected_stay_days,
            status=AdmissionStatus.ADMITTED,
            emergency_case_id=adm_in.emergency_case_id,
        )

        db.add(admission)
        db.flush()

        # Update bed to OCCUPIED and assign admission
        bed.status = BedStatus.OCCUPIED
        bed.current_admission_id = admission.id

        # If linked to emergency case, update ER status to ADMITTED_IPD
        if adm_in.emergency_case_id:
            emr = db.query(EmergencyCase).filter(EmergencyCase.id == adm_in.emergency_case_id).first()
            if emr:
                emr.status = EmergencyCaseStatus.ADMITTED_IPD

        db.commit()
        db.refresh(admission)

        AuditService.log(
            db=db,
            action="IPD_ADMISSION_CREATED",
            entity="ADMISSION",
            entity_id=str(admission.id),
            user_id=created_by_id,
            details={
                "admission_number": admission.admission_number,
                "patient_name": patient.full_name,
                "ward": ward.name,
                "bed": bed.bed_number,
            },
        )

        return IpdService.get_admission_response(admission)

    @staticmethod
    def transfer_bed(
        db: Session,
        admission_id: int,
        transfer_in: BedTransferCreate,
        transferred_by_id: Optional[int] = None,
    ) -> BedTransferResponse:
        """Transfer inpatient to a new Ward/Bed."""
        admission = db.query(Admission).filter(Admission.id == admission_id).first()
        if not admission or admission.status != AdmissionStatus.ADMITTED:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active admission not found.")

        old_bed = db.query(Bed).filter(Bed.id == admission.bed_id).first()
        new_bed = db.query(Bed).filter(Bed.id == transfer_in.to_bed_id).first()

        if not new_bed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target bed not found.")

        if new_bed.status == BedStatus.OCCUPIED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bed {new_bed.bed_number} is already occupied.")

        transfer_time = datetime.datetime.now(datetime.timezone.utc)

        transfer_log = BedTransfer(
            admission_id=admission.id,
            from_bed_id=old_bed.id if old_bed else new_bed.id,
            to_bed_id=new_bed.id,
            transfer_reason=transfer_in.transfer_reason,
            transferred_by_id=transferred_by_id,
            transferred_at=transfer_time,
        )
        db.add(transfer_log)

        # Free old bed to CLEANING
        if old_bed:
            old_bed.status = BedStatus.CLEANING
            old_bed.current_admission_id = None

        # Occupy new bed
        new_bed.status = BedStatus.OCCUPIED
        new_bed.current_admission_id = admission.id

        admission.bed_id = new_bed.id
        admission.ward_id = new_bed.ward_id

        db.commit()
        db.refresh(transfer_log)

        transferred_by_user = db.query(User).filter(User.id == transferred_by_id).first() if transferred_by_id else None

        AuditService.log(
            db=db,
            action="BED_TRANSFER",
            entity="ADMISSION",
            entity_id=str(admission.id),
            user_id=transferred_by_id,
            details={
                "from_bed": old_bed.bed_number if old_bed else "N/A",
                "to_bed": new_bed.bed_number,
                "reason": transfer_in.transfer_reason,
            },
        )

        return BedTransferResponse(
            id=transfer_log.id,
            admission_id=transfer_log.admission_id,
            from_bed_id=transfer_log.from_bed_id,
            to_bed_id=transfer_log.to_bed_id,
            from_bed_number=old_bed.bed_number if old_bed else None,
            to_bed_number=new_bed.bed_number,
            transfer_reason=transfer_log.transfer_reason,
            transferred_at=transfer_log.transferred_at,
            transferred_by_name=transferred_by_user.full_name if transferred_by_user else None,
        )

    @staticmethod
    def discharge_patient(
        db: Session,
        admission_id: int,
        discharge_in: DischargeRequest,
        discharged_by_id: Optional[int] = None,
    ) -> AdmissionResponse:
        """Process inpatient discharge and compile formal discharge summary."""
        admission = db.query(Admission).filter(Admission.id == admission_id).first()
        if not admission or admission.status != AdmissionStatus.ADMITTED:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active admission not found.")

        discharge_time = datetime.datetime.now(datetime.timezone.utc)

        admission.status = AdmissionStatus.DISCHARGED
        admission.discharge_date = discharge_time
        admission.discharge_diagnosis = discharge_in.discharge_diagnosis
        admission.discharge_summary = discharge_in.discharge_summary
        admission.discharge_condition = discharge_in.discharge_condition
        admission.discharge_medications = discharge_in.discharge_medications
        admission.follow_up_instructions = discharge_in.follow_up_instructions
        admission.discharged_by_id = discharged_by_id

        # Free bed to CLEANING
        bed = db.query(Bed).filter(Bed.id == admission.bed_id).first()
        if bed:
            bed.status = BedStatus.CLEANING
            bed.current_admission_id = None

        db.commit()
        db.refresh(admission)

        AuditService.log(
            db=db,
            action="IPD_DISCHARGE_COMPLETED",
            entity="ADMISSION",
            entity_id=str(admission.id),
            user_id=discharged_by_id,
            details={
                "admission_number": admission.admission_number,
                "discharge_condition": discharge_in.discharge_condition.value,
                "diagnosis": discharge_in.discharge_diagnosis,
            },
        )

        return IpdService.get_admission_response(admission)

    @staticmethod
    def get_admissions(
        db: Session,
        status: Optional[AdmissionStatus] = None,
        ward_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AdmissionResponse]:
        """Fetch list of inpatient admissions."""
        query = (
            db.query(Admission)
            .options(
                joinedload(Admission.patient),
                joinedload(Admission.admitting_doctor),
                joinedload(Admission.discharged_by),
                joinedload(Admission.ward),
                joinedload(Admission.bed),
            )
        )

        if status:
            query = query.filter(Admission.status == status)

        if ward_id:
            query = query.filter(Admission.ward_id == ward_id)

        if patient_id:
            query = query.filter(Admission.patient_id == patient_id)

        admissions = (
            query.order_by(desc(Admission.admission_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [IpdService.get_admission_response(a) for a in admissions]

    @staticmethod
    def get_admission_response(a: Admission) -> AdmissionResponse:
        return AdmissionResponse(
            id=a.id,
            admission_number=a.admission_number,
            patient_id=a.patient_id,
            admitting_doctor_id=a.admitting_doctor_id,
            ward_id=a.ward_id,
            bed_id=a.bed_id,
            admission_date=a.admission_date,
            discharge_date=a.discharge_date,
            admission_reason=a.admission_reason,
            expected_stay_days=a.expected_stay_days,
            status=a.status,
            emergency_case_id=a.emergency_case_id,
            discharge_diagnosis=a.discharge_diagnosis,
            discharge_summary=a.discharge_summary,
            discharge_condition=a.discharge_condition,
            discharge_medications=a.discharge_medications or [],
            follow_up_instructions=a.follow_up_instructions,
            discharged_by_id=a.discharged_by_id,
            patient_name=a.patient.full_name if a.patient else "Patient",
            patient_mrn=a.patient.mrn if a.patient else "",
            doctor_name=a.admitting_doctor.full_name if a.admitting_doctor else "Doctor",
            ward_name=a.ward.name if a.ward else "General Ward",
            bed_number=a.bed.bed_number if a.bed else "Bed",
            discharged_by_name=a.discharged_by.full_name if a.discharged_by else None,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
