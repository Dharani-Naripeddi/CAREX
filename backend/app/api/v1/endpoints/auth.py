from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user, get_client_ip
from app.schemas.auth import LoginRequest, Token, UserProfile
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=Token, summary="Authenticate and obtain JWT bearer token")
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate with email and password.
    Returns access token and full user profile with role permissions.
    """
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    return AuthService.authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password,
        ip_address=ip,
        user_agent=user_agent,
    )


@router.get("/me", response_model=UserProfile, summary="Get current authenticated user profile")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Return the profile and permissions of the currently authenticated user."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.name,
        role_display_name=current_user.role.display_name,
        permissions=current_user.role.permissions or [],
        department_name=current_user.department.name if current_user.department else None,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
    )


@router.post("/logout", response_model=APIResponse[dict], summary="Logout current user")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log out the current user session and write audit trail."""
    ip = get_client_ip(request)
    AuditService.log(
        db=db,
        action="LOGOUT",
        entity="AUTH",
        entity_id=str(current_user.id),
        user_id=current_user.id,
        details={"email": current_user.email},
        ip_address=ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return APIResponse(
        success=True,
        message="Logged out successfully",
        data={"user_id": current_user.id},
    )
