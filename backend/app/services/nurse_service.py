from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.nurse_profile import NurseProfile, ShiftEnum
from app.models.user import User
from app.schemas.nurse import NurseProfileCreate, NurseProfileUpdate, NurseWithUser


class NurseService:
    @staticmethod
    def get_nurses(
        db: Session,
        department_id: Optional[int] = None,
        shift: Optional[ShiftEnum] = None,
        is_on_duty: Optional[bool] = None,
    ) -> List[NurseWithUser]:
        """List all nurses with profile and shift info."""
        query = (
            db.query(NurseProfile)
            .options(
                joinedload(NurseProfile.user),
                joinedload(NurseProfile.department),
            )
        )

        if department_id:
            query = query.filter(NurseProfile.department_id == department_id)

        if shift:
            query = query.filter(NurseProfile.shift == shift)

        if is_on_duty is not None:
            query = query.filter(NurseProfile.is_on_duty == is_on_duty)

        profiles = query.all()

        results = []
        for p in profiles:
            results.append(
                NurseWithUser(
                    id=p.id,
                    user_id=p.user_id,
                    qualification=p.qualification,
                    shift=p.shift,
                    ward_assigned=p.ward_assigned,
                    is_on_duty=p.is_on_duty,
                    department_id=p.department_id,
                    full_name=p.user.full_name if p.user else "Nurse Staff",
                    email=p.user.email if p.user else "",
                    avatar_url=p.user.avatar_url if p.user else None,
                    department_name=p.department.name if p.department else None,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
            )
        return results

    @staticmethod
    def get_nurse_by_user_id(db: Session, user_id: int) -> Optional[NurseWithUser]:
        """Fetch nurse profile by user ID."""
        p = (
            db.query(NurseProfile)
            .options(joinedload(NurseProfile.user), joinedload(NurseProfile.department))
            .filter(NurseProfile.user_id == user_id)
            .first()
        )
        if not p:
            return None

        return NurseWithUser(
            id=p.id,
            user_id=p.user_id,
            qualification=p.qualification,
            shift=p.shift,
            ward_assigned=p.ward_assigned,
            is_on_duty=p.is_on_duty,
            department_id=p.department_id,
            full_name=p.user.full_name if p.user else "Nurse Staff",
            email=p.user.email if p.user else "",
            avatar_url=p.user.avatar_url if p.user else None,
            department_name=p.department.name if p.department else None,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    @staticmethod
    def register_nurse(
        db: Session,
        nurse_in,
    ) -> NurseWithUser:
        """Register a new nurse account and roster profile."""
        from app.models.role import Role, RoleEnum
        from app.core.security import get_password_hash

        role = db.query(Role).filter(Role.name == RoleEnum.NURSE).first()
        if not role:
            raise HTTPException(status_code=500, detail="Nurse role not configured.")

        # Check existing user by email
        user = db.query(User).filter(User.email == nurse_in.email.strip().lower()).first()
        if not user:
            user = User(
                email=nurse_in.email.strip().lower(),
                hashed_password=get_password_hash(nurse_in.password or "Carex#2026"),
                full_name=nurse_in.full_name.strip(),
                phone=nurse_in.phone or "+1-555-0199",
                avatar_url=nurse_in.avatar_url or "https://images.unsplash.com/photo-1594824813501-489e5a8f5f84?w=150&auto=format&fit=crop&q=80",
                role_id=role.id,
                department_id=nurse_in.department_id,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.department_id = nurse_in.department_id
            user.full_name = nurse_in.full_name.strip()
            db.commit()

        # Create or update profile
        profile = db.query(NurseProfile).filter(NurseProfile.user_id == user.id).first()
        if not profile:
            profile = NurseProfile(
                user_id=user.id,
                department_id=nurse_in.department_id,
                qualification=nurse_in.qualification.strip(),
                shift=nurse_in.shift,
                ward_assigned=nurse_in.ward_assigned or "General Inpatient Ward",
                is_on_duty=nurse_in.is_on_duty,
            )
            db.add(profile)
        else:
            profile.department_id = nurse_in.department_id
            profile.qualification = nurse_in.qualification.strip()
            profile.shift = nurse_in.shift
            profile.ward_assigned = nurse_in.ward_assigned or "General Inpatient Ward"
            profile.is_on_duty = nurse_in.is_on_duty

        db.commit()
        db.refresh(profile)

        nurse_res = NurseService.get_nurse_by_user_id(db, user.id)
        if not nurse_res:
            raise HTTPException(status_code=500, detail="Failed to load registered nurse profile.")
        return nurse_res

    @staticmethod
    def create_or_update_nurse_profile(
        db: Session,
        user_id: int,
        profile_in: NurseProfileUpdate,
    ) -> NurseProfile:
        """Create or update a nurse profile for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )

        profile = db.query(NurseProfile).filter(NurseProfile.user_id == user_id).first()
        if not profile:
            profile = NurseProfile(
                user_id=user_id,
                qualification=profile_in.qualification or "BSN, RN",
                shift=profile_in.shift or ShiftEnum.MORNING,
                ward_assigned=profile_in.ward_assigned or "General Inpatient Ward",
                is_on_duty=profile_in.is_on_duty if profile_in.is_on_duty is not None else True,
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


