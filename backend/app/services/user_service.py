from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.services.audit_service import AuditService


class UserService:
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Fetch list of users with role and department relationships."""
        return (
            db.query(User)
            .options(joinedload(User.role), joinedload(User.department))
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Fetch user by primary ID."""
        return (
            db.query(User)
            .options(joinedload(User.role), joinedload(User.department))
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch user by unique email."""
        return (
            db.query(User)
            .options(joinedload(User.role), joinedload(User.department))
            .filter(User.email == email.lower().strip())
            .first()
        )

    @staticmethod
    def create_user(db: Session, user_in: UserCreate, created_by_id: Optional[int] = None) -> User:
        """Create new user with hashed password."""
        existing = UserService.get_user_by_email(db, user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{user_in.email}' already exists.",
            )

        role = db.query(Role).filter(Role.id == user_in.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with ID {user_in.role_id} does not exist.",
            )

        db_user = User(
            email=user_in.email.lower().strip(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            phone=user_in.phone,
            avatar_url=user_in.avatar_url,
            is_active=user_in.is_active,
            is_verified=user_in.is_verified,
            role_id=user_in.role_id,
            department_id=user_in.department_id,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        AuditService.log(
            db=db,
            action="CREATE_USER",
            entity="USER",
            entity_id=str(db_user.id),
            user_id=created_by_id,
            details={"email": db_user.email, "role": role.name.value},
        )

        return db_user

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        user_in: UserUpdate,
        updated_by_id: Optional[int] = None,
    ) -> User:
        """Update existing user profile fields."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )

        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        AuditService.log(
            db=db,
            action="UPDATE_USER",
            entity="USER",
            entity_id=str(user.id),
            user_id=updated_by_id,
            details=update_data,
        )

        return user
