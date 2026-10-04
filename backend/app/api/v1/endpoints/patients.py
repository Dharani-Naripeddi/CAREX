from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services.patient_service import PatientService

router = APIRouter()


@router.get(
    "/",
    response_model=List[PatientResponse],
    summary="Search and filter patients",
)
def list_patients(
    query: Optional[str] = Query(None, description="Search by name, MRN, phone, email"),
    gender: Optional[str] = Query(None, description="Filter by gender (Male, Female, Other)"),
    blood_group: Optional[str] = Query(None, description="Filter by blood group (A+, O+, etc.)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve filtered patient records from Master Patient Index (MPI)."""
    # Patients can only see their own record if calling this list
    if current_user.role and current_user.role.name == RoleEnum.PATIENT:
        p = PatientService.get_patient_by_user_id(db, current_user.id)
        return [p] if p else []

    return PatientService.get_patients(
        db=db,
        query=query,
        gender=gender,
        blood_group=blood_group,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.RECEPTIONIST,
                RoleEnum.DOCTOR,
                RoleEnum.NURSE,
                RoleEnum.PATIENT,
            )
        )
    ],
)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Register a new patient and generate unique MRN."""
    return PatientService.create_patient(
        db=db,
        patient_in=patient_in,
        registered_by_id=current_user.id,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get patient profile by ID",
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve full patient clinical profile including allergies and history."""
    patient = PatientService.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found.",
        )

    # If patient role, ensure accessing own record
    if current_user.role and current_user.role.name == RoleEnum.PATIENT:
        if patient.user_id != current_user.id and patient.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you may only access your own medical records.",
            )

    return patient


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update patient profile",
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.SUPER_ADMIN,
                RoleEnum.HOSPITAL_ADMIN,
                RoleEnum.RECEPTIONIST,
                RoleEnum.DOCTOR,
                RoleEnum.NURSE,
            )
        )
    ],
)
def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update patient demographics, emergency contact, allergies, or medications."""
    return PatientService.update_patient(
        db=db,
        patient_id=patient_id,
        patient_in=patient_in,
        updated_by_id=current_user.id,
    )


@router.get(
    "/{patient_id}/journey",
    summary="Get unified end-to-end patient care journey timeline",
)
def get_patient_journey_timeline(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve the full chronological care journey across Registration, Appointments, OPD, Doctor, Lab, Pharmacy, Inpatient, and Billing."""
    # If patient role, ensure accessing own record
    patient = PatientService.get_patient_by_id(db, patient_id)
    if not patient:
        # Try finding first patient
        patient = db.query(Patient).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient record {patient_id} not found.",
            )

    if current_user.role and current_user.role.name == RoleEnum.PATIENT:
        if patient.user_id != current_user.id and patient.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you may only access your own patient care journey.",
            )

    from app.demo.service import DemoService
    journey = DemoService.get_patient_journey(
        db=db,
        patient_id=patient.id,
        role=current_user.role.name if current_user.role else None,
    )
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient journey data could not be compiled for patient {patient_id}.",
        )
    return journey
