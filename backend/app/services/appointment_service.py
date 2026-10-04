import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from fastapi import HTTPException, status
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.patient import Patient
from app.models.user import User
from app.models.department import Department
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatusUpdate,
    AppointmentReschedule,
    AppointmentWithDetails,
)
from app.services.audit_service import AuditService


class AppointmentService:
    @staticmethod
    def generate_appointment_number(db: Session) -> str:
        """Generate unique sequential appointment number format: APT-YYYY-XXXX."""
        current_year = datetime.date.today().year
        prefix = f"APT-{current_year}-"

        latest = (
            db.query(Appointment)
            .filter(Appointment.appointment_number.like(f"{prefix}%"))
            .order_by(desc(Appointment.id))
            .first()
        )

        if latest and latest.appointment_number.startswith(prefix):
            try:
                seq = int(latest.appointment_number.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:04d}"

    @staticmethod
    def get_appointments(
        db: Session,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        department_id: Optional[int] = None,
        date: Optional[datetime.date] = None,
        status: Optional[AppointmentStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AppointmentWithDetails]:
        """Fetch list of appointments with eager loaded relations."""
        query = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor),
                joinedload(Appointment.department),
            )
        )

        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)

        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)

        if department_id:
            query = query.filter(Appointment.department_id == department_id)

        if date:
            query = query.filter(Appointment.appointment_date == date)

        if status:
            query = query.filter(Appointment.status == status)

        appointments = (
            query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        results = []
        for a in appointments:
            results.append(
                AppointmentWithDetails(
                    id=a.id,
                    appointment_number=a.appointment_number,
                    patient_id=a.patient_id,
                    doctor_id=a.doctor_id,
                    department_id=a.department_id,
                    appointment_date=a.appointment_date,
                    appointment_time=a.appointment_time,
                    type=a.type,
                    status=a.status,
                    chief_complaint=a.chief_complaint,
                    notes=a.notes,
                    cancellation_reason=a.cancellation_reason,
                    created_by_id=a.created_by_id,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                    patient_name=a.patient.full_name if a.patient else "Unknown Patient",
                    patient_mrn=a.patient.mrn if a.patient else "",
                    patient_phone=a.patient.phone if a.patient else "",
                    doctor_name=a.doctor.full_name if a.doctor else "Unknown Doctor",
                    department_name=a.department.name if a.department else "General",
                )
            )
        return results

    @staticmethod
    def get_appointment_by_id(db: Session, appointment_id: int) -> Optional[Appointment]:
        """Fetch appointment by ID."""
        return (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor),
                joinedload(Appointment.department),
            )
            .filter(Appointment.id == appointment_id)
            .first()
        )

    @staticmethod
    def create_appointment(
        db: Session,
        app_in: AppointmentCreate,
        created_by_id: Optional[int] = None,
    ) -> Appointment:
        """Create a new appointment with validation."""
        patient = db.query(Patient).filter(Patient.id == app_in.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {app_in.patient_id} not found.",
            )

        doctor = db.query(User).filter(User.id == app_in.doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {app_in.doctor_id} not found.",
            )

        department = db.query(Department).filter(Department.id == app_in.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {app_in.department_id} not found.",
            )

        appointment_number = AppointmentService.generate_appointment_number(db)

        appointment = Appointment(
            appointment_number=appointment_number,
            patient_id=app_in.patient_id,
            doctor_id=app_in.doctor_id,
            department_id=app_in.department_id,
            appointment_date=app_in.appointment_date,
            appointment_time=app_in.appointment_time,
            type=app_in.type,
            status=AppointmentStatus.SCHEDULED,
            chief_complaint=app_in.chief_complaint,
            notes=app_in.notes,
            created_by_id=created_by_id,
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        AuditService.log(
            db=db,
            action="APPOINTMENT_CREATED",
            entity="APPOINTMENT",
            entity_id=str(appointment.id),
            user_id=created_by_id,
            details={
                "appointment_number": appointment.appointment_number,
                "patient_id": patient.id,
                "doctor_id": doctor.id,
                "date": str(appointment.appointment_date),
            },
        )

        return appointment

    @staticmethod
    def update_appointment_status(
        db: Session,
        appointment_id: int,
        status_in: AppointmentStatusUpdate,
        updated_by_id: Optional[int] = None,
    ) -> Appointment:
        """Update appointment lifecycle status."""
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found.",
            )

        appointment.status = status_in.status
        if status_in.cancellation_reason:
            appointment.cancellation_reason = status_in.cancellation_reason
        if status_in.notes:
            appointment.notes = status_in.notes

        db.commit()
        db.refresh(appointment)

        AuditService.log(
            db=db,
            action=f"APPOINTMENT_STATUS_{status_in.status.value}",
            entity="APPOINTMENT",
            entity_id=str(appointment.id),
            user_id=updated_by_id,
            details={"status": status_in.status.value},
        )

        return appointment

    @staticmethod
    def reschedule_appointment(
        db: Session,
        appointment_id: int,
        reschedule_in: AppointmentReschedule,
        updated_by_id: Optional[int] = None,
    ) -> Appointment:
        """Reschedule date and time of appointment."""
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found.",
            )

        if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reschedule appointment with status '{appointment.status.value}'.",
            )

        appointment.appointment_date = reschedule_in.appointment_date
        appointment.appointment_time = reschedule_in.appointment_time
        if reschedule_in.notes:
            appointment.notes = reschedule_in.notes

        db.commit()
        db.refresh(appointment)

        AuditService.log(
            db=db,
            action="APPOINTMENT_RESCHEDULED",
            entity="APPOINTMENT",
            entity_id=str(appointment.id),
            user_id=updated_by_id,
            details={
                "new_date": str(reschedule_in.appointment_date),
                "new_time": reschedule_in.appointment_time,
            },
        )

        return appointment
