import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_
from fastapi import HTTPException, status
from app.models.opd_token import OpdToken, TokenStatus, TokenPriority
from app.models.appointment import Appointment, AppointmentStatus
from app.models.department import Department
from app.models.patient import Patient
from app.models.user import User
from app.schemas.opd_token import (
    TokenGenerateRequest,
    TokenWithDetails,
    TokenQueueStatus,
    PatientLiveTokenStatus,
)
from app.services.audit_service import AuditService


class TokenService:
    @staticmethod
    def generate_token(
        db: Session,
        token_in: TokenGenerateRequest,
        generated_by_id: Optional[int] = None,
    ) -> OpdToken:
        """Generate a new OPD queue token with daily sequential number and estimated wait time."""
        today = datetime.date.today()

        patient = db.query(Patient).filter(Patient.id == token_in.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {token_in.patient_id} not found.",
            )

        department = db.query(Department).filter(Department.id == token_in.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {token_in.department_id} not found.",
            )

        # Compute next daily sequence number for this department today
        max_seq = (
            db.query(func.max(OpdToken.token_number))
            .filter(
                OpdToken.department_id == token_in.department_id,
                OpdToken.date == today,
            )
            .scalar()
        )
        next_seq = (max_seq or 0) + 1

        dept_code_short = department.code[:4].upper()
        token_code = f"{dept_code_short}-{next_seq:03d}"

        # Calculate estimated wait time based on waiting tokens ahead
        waiting_count = (
            db.query(OpdToken)
            .filter(
                OpdToken.department_id == token_in.department_id,
                OpdToken.date == today,
                OpdToken.status.in_([TokenStatus.ISSUED, TokenStatus.CALLED]),
            )
            .count()
        )
        estimated_wait = max(5, waiting_count * 12)  # ~12 mins average consultation

        token = OpdToken(
            token_number=next_seq,
            token_code=token_code,
            date=today,
            patient_id=token_in.patient_id,
            doctor_id=token_in.doctor_id,
            department_id=token_in.department_id,
            appointment_id=token_in.appointment_id,
            priority=token_in.priority,
            status=TokenStatus.ISSUED,
            estimated_wait_minutes=estimated_wait,
        )

        db.add(token)

        # If linked to an appointment, transition appointment to CHECKED_IN or WAITING
        if token_in.appointment_id:
            appt = db.query(Appointment).filter(Appointment.id == token_in.appointment_id).first()
            if appt and appt.status == AppointmentStatus.SCHEDULED:
                appt.status = AppointmentStatus.WAITING

        db.commit()
        db.refresh(token)

        AuditService.log(
            db=db,
            action="TOKEN_GENERATED",
            entity="OPD_TOKEN",
            entity_id=str(token.id),
            user_id=generated_by_id,
            details={
                "token_code": token.token_code,
                "patient_id": patient.id,
                "department": department.name,
                "wait_minutes": estimated_wait,
            },
        )

        return token

    @staticmethod
    def get_token_queue_status(
        db: Session,
        department_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
    ) -> TokenQueueStatus:
        """Fetch real-time waiting queue, current token, and patient roster."""
        today = datetime.date.today()

        query = (
            db.query(OpdToken)
            .options(
                joinedload(OpdToken.patient),
                joinedload(OpdToken.doctor),
                joinedload(OpdToken.department),
            )
            .filter(OpdToken.date == today)
        )

        dept_name = "All Hospital Departments"
        doc_name = None

        if department_id:
            query = query.filter(OpdToken.department_id == department_id)
            dept = db.query(Department).filter(Department.id == department_id).first()
            if dept:
                dept_name = dept.name

        if doctor_id:
            query = query.filter(OpdToken.doctor_id == doctor_id)
            doc = db.query(User).filter(User.id == doctor_id).first()
            if doc:
                doc_name = doc.full_name

        all_tokens = query.order_by(OpdToken.token_number.asc()).all()

        # Find current active token (IN_ROOM or CALLED)
        current_token = None
        for t in all_tokens:
            if t.status in [TokenStatus.IN_ROOM, TokenStatus.CALLED]:
                current_token = t
                break

        # Filter waiting tokens
        waiting_tokens = [t for t in all_tokens if t.status in [TokenStatus.ISSUED, TokenStatus.CALLED, TokenStatus.IN_ROOM]]

        token_details_list = []
        for t in waiting_tokens:
            token_details_list.append(
                TokenWithDetails(
                    id=t.id,
                    token_number=t.token_number,
                    token_code=t.token_code,
                    date=t.date,
                    patient_id=t.patient_id,
                    doctor_id=t.doctor_id,
                    department_id=t.department_id,
                    appointment_id=t.appointment_id,
                    priority=t.priority,
                    status=t.status,
                    estimated_wait_minutes=t.estimated_wait_minutes,
                    called_at=t.called_at,
                    serviced_at=t.serviced_at,
                    created_at=t.created_at,
                    patient_name=t.patient.full_name if t.patient else "Patient",
                    patient_mrn=t.patient.mrn if t.patient else "",
                    doctor_name=t.doctor.full_name if t.doctor else None,
                    department_name=t.department.name if t.department else "General",
                )
            )

        return TokenQueueStatus(
            department_name=dept_name,
            doctor_name=doc_name,
            current_token_code=current_token.token_code if current_token else None,
            current_token_number=current_token.token_number if current_token else None,
            total_in_queue=len(waiting_tokens),
            waiting_tokens=token_details_list,
        )

    @staticmethod
    def get_patient_live_token_status(db: Session, patient_id: int) -> PatientLiveTokenStatus:
        """Calculate live token state, patients ahead, and estimated wait for a specific patient."""
        today = datetime.date.today()

        # Find active token for today
        patient_token = (
            db.query(OpdToken)
            .options(
                joinedload(OpdToken.patient),
                joinedload(OpdToken.doctor),
                joinedload(OpdToken.department),
            )
            .filter(
                OpdToken.patient_id == patient_id,
                OpdToken.date == today,
                OpdToken.status.in_([TokenStatus.ISSUED, TokenStatus.CALLED, TokenStatus.IN_ROOM]),
            )
            .order_by(desc(OpdToken.id))
            .first()
        )

        if not patient_token:
            return PatientLiveTokenStatus(has_active_token=False)

        # Count tokens ahead with earlier sequence number and still in waiting/called status
        patients_ahead = (
            db.query(OpdToken)
            .filter(
                OpdToken.department_id == patient_token.department_id,
                OpdToken.date == today,
                OpdToken.token_number < patient_token.token_number,
                OpdToken.status.in_([TokenStatus.ISSUED, TokenStatus.CALLED]),
            )
            .count()
        )

        # Current serving token in this department
        current_serving = (
            db.query(OpdToken)
            .filter(
                OpdToken.department_id == patient_token.department_id,
                OpdToken.date == today,
                OpdToken.status.in_([TokenStatus.IN_ROOM, TokenStatus.CALLED]),
            )
            .order_by(desc(OpdToken.called_at))
            .first()
        )

        estimated_wait = max(0, patients_ahead * 12)
        if patient_token.status == TokenStatus.CALLED:
            estimated_wait = 0

        token_details = TokenWithDetails(
            id=patient_token.id,
            token_number=patient_token.token_number,
            token_code=patient_token.token_code,
            date=patient_token.date,
            patient_id=patient_token.patient_id,
            doctor_id=patient_token.doctor_id,
            department_id=patient_token.department_id,
            appointment_id=patient_token.appointment_id,
            priority=patient_token.priority,
            status=patient_token.status,
            estimated_wait_minutes=estimated_wait,
            called_at=patient_token.called_at,
            serviced_at=patient_token.serviced_at,
            created_at=patient_token.created_at,
            patient_name=patient_token.patient.full_name if patient_token.patient else "",
            patient_mrn=patient_token.patient.mrn if patient_token.patient else "",
            doctor_name=patient_token.doctor.full_name if patient_token.doctor else None,
            department_name=patient_token.department.name if patient_token.department else "General",
        )

        return PatientLiveTokenStatus(
            has_active_token=True,
            token=token_details,
            current_serving_token_code=current_serving.token_code if current_serving else None,
            patients_ahead=patients_ahead,
            estimated_wait_minutes=estimated_wait,
        )

    @staticmethod
    def call_token(db: Session, token_id: int, called_by_id: Optional[int] = None) -> OpdToken:
        """Call token into consultation room."""
        token = db.query(OpdToken).filter(OpdToken.id == token_id).first()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token with ID {token_id} not found.",
            )

        token.status = TokenStatus.CALLED
        token.called_at = datetime.datetime.now(datetime.timezone.utc)

        if token.appointment_id:
            appt = db.query(Appointment).filter(Appointment.id == token.appointment_id).first()
            if appt:
                appt.status = AppointmentStatus.IN_CONSULTATION

        db.commit()
        db.refresh(token)

        AuditService.log(
            db=db,
            action="TOKEN_CALLED",
            entity="OPD_TOKEN",
            entity_id=str(token.id),
            user_id=called_by_id,
            details={"token_code": token.token_code, "status": "CALLED"},
        )

        return token

    @staticmethod
    def complete_token(db: Session, token_id: int, completed_by_id: Optional[int] = None) -> OpdToken:
        """Mark token consultation completed."""
        token = db.query(OpdToken).filter(OpdToken.id == token_id).first()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token with ID {token_id} not found.",
            )

        token.status = TokenStatus.SERVICED
        token.serviced_at = datetime.datetime.now(datetime.timezone.utc)

        if token.appointment_id:
            appt = db.query(Appointment).filter(Appointment.id == token.appointment_id).first()
            if appt:
                appt.status = AppointmentStatus.COMPLETED

        db.commit()
        db.refresh(token)

        AuditService.log(
            db=db,
            action="TOKEN_SERVICED",
            entity="OPD_TOKEN",
            entity_id=str(token.id),
            user_id=completed_by_id,
            details={"token_code": token.token_code, "status": "SERVICED"},
        )

        return token
