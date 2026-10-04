from typing import Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import LoginRequest, Token, UserProfile
from app.services.audit_service import AuditService
from app.core.config import settings


class AuthService:
    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Token:
        """Authenticate user by email and password, generate JWT and audit log."""
        user = (
            db.query(User)
            .options(joinedload(User.role), joinedload(User.department))
            .filter(User.email == email.lower().strip())
            .first()
        )

        if not user or not verify_password(password, user.hashed_password):
            AuditService.log(
                db=db,
                action="LOGIN_FAILED",
                entity="AUTH",
                details={"attempted_email": email},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Contact hospital administration.",
            )

        role_name = user.role.name.value if hasattr(user.role.name, "value") else str(user.role.name)
        access_token = create_access_token(
            subject=user.id,
            role=role_name,
            extra_claims={
                "email": user.email,
                "full_name": user.full_name,
                "role_display": user.role.display_name,
            },
        )

        # Audit successful login
        AuditService.log(
            db=db,
            action="LOGIN_SUCCESS",
            entity="AUTH",
            entity_id=str(user.id),
            user_id=user.id,
            details={"email": user.email, "role": role_name},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        user_profile = UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.name,
            role_display_name=user.role.display_name,
            permissions=user.role.permissions or [],
            department_name=user.department.name if user.department else None,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_profile,
        )
