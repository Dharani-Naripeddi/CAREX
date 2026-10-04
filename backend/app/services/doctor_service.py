from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.doctor_profile import DoctorProfile
from app.models.user import User
from app.models.department import Department
from app.models.role import RoleEnum
from app.schemas.doctor import DoctorProfileCreate, DoctorProfileUpdate, DoctorWithUser, DoctorCreate


class DoctorService:
    @staticmethod
    def get_doctors(
        db: Session,
        department_id: Optional[int] = None,
        is_available: Optional[bool] = None,
    ) -> List[DoctorWithUser]:
        """List all doctors with user account info and department metadata."""
        query = (
            db.query(DoctorProfile)
            .options(
                joinedload(DoctorProfile.user),
                joinedload(DoctorProfile.department),
            )
        )

        if department_id:
            query = query.filter(DoctorProfile.department_id == department_id)

        if is_available is not None:
            query = query.filter(DoctorProfile.is_available == is_available)

        profiles = query.all()

        results = []
        for p in profiles:
            results.append(
                DoctorWithUser(
                    id=p.id,
                    user_id=p.user_id,
                    specialization=p.specialization,
                    qualification=p.qualification,
                    experience_years=p.experience_years,
                    consultation_fee=p.consultation_fee,
                    room_number=p.room_number,
                    availability_days=p.availability_days or [],
                    available_from=p.available_from,
                    available_to=p.available_to,
                    is_available=p.is_available,
                    department_id=p.department_id,
                    full_name=p.user.full_name if p.user else "Unknown Doctor",
                    email=p.user.email if p.user else "",
                    avatar_url=p.user.avatar_url if p.user else None,
                    department_name=p.department.name if p.department else None,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
            )
        return results

    @staticmethod
    def get_doctor_by_user_id(db: Session, user_id: int) -> Optional[DoctorWithUser]:
        """Fetch doctor profile by user ID."""
        p = (
            db.query(DoctorProfile)
            .options(joinedload(DoctorProfile.user), joinedload(DoctorProfile.department))
            .filter(DoctorProfile.user_id == user_id)
            .first()
        )
        if not p:
            return None

        return DoctorWithUser(
            id=p.id,
            user_id=p.user_id,
            specialization=p.specialization,
            qualification=p.qualification,
            experience_years=p.experience_years,
            consultation_fee=p.consultation_fee,
            room_number=p.room_number,
            availability_days=p.availability_days or [],
            available_from=p.available_from,
            available_to=p.available_to,
            is_available=p.is_available,
            department_id=p.department_id,
            full_name=p.user.full_name if p.user else "Unknown Doctor",
            email=p.user.email if p.user else "",
            avatar_url=p.user.avatar_url if p.user else None,
            department_name=p.department.name if p.department else None,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    @staticmethod
    def create_or_update_doctor_profile(
        db: Session,
        user_id: int,
        profile_in: DoctorProfileUpdate,
    ) -> DoctorProfile:
        """Create or update a doctor profile for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )

        profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()
        if not profile:
            profile = DoctorProfile(
                user_id=user_id,
                specialization=profile_in.specialization or "General Medicine",
                qualification=profile_in.qualification or "MBBS",
                experience_years=profile_in.experience_years or 5,
                consultation_fee=profile_in.consultation_fee or 75.0,
                room_number=profile_in.room_number,
                availability_days=profile_in.availability_days or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                available_from=profile_in.available_from or "09:00",
                available_to=profile_in.available_to or "17:00",
                is_available=profile_in.is_available if profile_in.is_available is not None else True,
                department_id=profile_in.department_id or user.department_id,
            )
            db.add(profile)
        else:
            update_data = profile_in.model_dump(exclude_unset=True)
            for field, val in update_data.items():
                setattr(profile, field, val)

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def register_doctor(
        db: Session,
        doctor_in: DoctorCreate,
    ) -> DoctorWithUser:
        """Register a new doctor account and clinical profile."""
        from app.models.role import Role
        from app.core.security import get_password_hash

        role = db.query(Role).filter(Role.name == RoleEnum.DOCTOR).first()
        if not role:
            raise HTTPException(status_code=500, detail="Doctor role not configured.")

        # Check existing user by email
        user = db.query(User).filter(User.email == doctor_in.email.strip().lower()).first()
        if not user:
            user = User(
                email=doctor_in.email.strip().lower(),
                hashed_password=get_password_hash(doctor_in.password or "Carex#2026"),
                full_name=doctor_in.full_name.strip(),
                phone=doctor_in.phone or "+1-555-0199",
                avatar_url=doctor_in.avatar_url or "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150&auto=format&fit=crop&q=80",
                role_id=role.id,
                department_id=doctor_in.department_id,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.department_id = doctor_in.department_id
            user.full_name = doctor_in.full_name.strip()
            db.commit()

        # Create or update profile
        profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
        if not profile:
            profile = DoctorProfile(
                user_id=user.id,
                department_id=doctor_in.department_id,
                specialization=doctor_in.specialization.strip(),
                qualification=doctor_in.qualification.strip(),
                experience_years=doctor_in.experience_years,
                consultation_fee=doctor_in.consultation_fee,
                room_number=doctor_in.room_number,
                availability_days=doctor_in.availability_days or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                available_from=doctor_in.available_from,
                available_to=doctor_in.available_to,
                is_available=True,
            )
            db.add(profile)
        else:
            profile.department_id = doctor_in.department_id
            profile.specialization = doctor_in.specialization.strip()
            profile.qualification = doctor_in.qualification.strip()
            profile.experience_years = doctor_in.experience_years
            profile.consultation_fee = doctor_in.consultation_fee
            profile.room_number = doctor_in.room_number
            profile.availability_days = doctor_in.availability_days or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            profile.available_from = doctor_in.available_from
            profile.available_to = doctor_in.available_to

        db.commit()
        db.refresh(profile)

        doc = DoctorService.get_doctor_by_user_id(db, user.id)
        if not doc:
            raise HTTPException(status_code=500, detail="Failed to load created doctor profile.")
        return doc

