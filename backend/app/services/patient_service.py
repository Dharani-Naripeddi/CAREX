import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException, status
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.audit_service import AuditService


class PatientService:
    @staticmethod
    def generate_mrn(db: Session) -> str:
        """Generate unique sequential Medical Record Number (MRN) format: CRX-YYYY-XXXX."""
        current_year = datetime.date.today().year
        prefix = f"CRX-{current_year}-"

        # Find the latest patient MRN with this prefix
        latest = (
            db.query(Patient)
            .filter(Patient.mrn.like(f"{prefix}%"))
            .order_by(desc(Patient.id))
            .first()
        )

        if latest and latest.mrn.startswith(prefix):
            try:
                seq = int(latest.mrn.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:04d}"

    @staticmethod
    def get_patients(
        db: Session,
        query: Optional[str] = None,
        gender: Optional[str] = None,
        blood_group: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Patient]:
        """Search and filter patient records."""
        db_query = db.query(Patient)

        if query:
            search_term = f"%{query.strip()}%"
            db_query = db_query.filter(
                or_(
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                    Patient.mrn.ilike(search_term),
                    Patient.phone.ilike(search_term),
                    Patient.email.ilike(search_term),
                )
            )

        if gender:
            db_query = db_query.filter(Patient.gender == gender)

        if blood_group:
            db_query = db_query.filter(Patient.blood_group == blood_group)

        return db_query.order_by(desc(Patient.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def get_patient_by_id(db: Session, patient_id: int) -> Optional[Patient]:
        """Fetch patient record by ID."""
        return db.query(Patient).filter(Patient.id == patient_id).first()

    @staticmethod
    def get_patient_by_mrn(db: Session, mrn: str) -> Optional[Patient]:
        """Fetch patient record by MRN."""
        return db.query(Patient).filter(Patient.mrn == mrn.strip()).first()

    @staticmethod
    def get_patient_by_user_id(db: Session, user_id: int) -> Optional[Patient]:
        """Fetch patient linked to a login user account."""
        return db.query(Patient).filter(Patient.user_id == user_id).first()

    @staticmethod
    def create_patient(
        db: Session,
        patient_in: PatientCreate,
        registered_by_id: Optional[int] = None,
    ) -> Patient:
        """Register a new patient with auto-generated MRN."""
        mrn = PatientService.generate_mrn(db)

        patient = Patient(
            mrn=mrn,
            first_name=patient_in.first_name.strip(),
            last_name=patient_in.last_name.strip(),
            email=patient_in.email.lower().strip() if patient_in.email else None,
            phone=patient_in.phone.strip(),
            date_of_birth=patient_in.date_of_birth,
            gender=patient_in.gender,
            blood_group=patient_in.blood_group,
            address=patient_in.address,
            emergency_contact_name=patient_in.emergency_contact_name,
            emergency_contact_phone=patient_in.emergency_contact_phone,
            emergency_contact_relation=patient_in.emergency_contact_relation,
            allergies=patient_in.allergies or [],
            current_medications=patient_in.current_medications or [],
            medical_history=patient_in.medical_history or [],
            user_id=patient_in.user_id,
            registered_by_id=registered_by_id,
        )

        db.add(patient)
        db.commit()
        db.refresh(patient)

        AuditService.log(
            db=db,
            action="PATIENT_REGISTERED",
            entity="PATIENT",
            entity_id=str(patient.id),
            user_id=registered_by_id,
            details={"mrn": patient.mrn, "full_name": patient.full_name},
        )

        return patient

    @staticmethod
    def update_patient(
        db: Session,
        patient_id: int,
        patient_in: PatientUpdate,
        updated_by_id: Optional[int] = None,
    ) -> Patient:
        """Update existing patient details."""
        patient = PatientService.get_patient_by_id(db, patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found.",
            )

        update_data = patient_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "email" and value:
                value = value.lower().strip()
            setattr(patient, field, value)

        db.commit()
        db.refresh(patient)

        AuditService.log(
            db=db,
            action="PATIENT_UPDATED",
            entity="PATIENT",
            entity_id=str(patient.id),
            user_id=updated_by_id,
            details=update_data,
        )

        return patient
