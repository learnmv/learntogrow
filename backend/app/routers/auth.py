from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.services import AuthService, create_access_token, decode_token
from app.schemas.auth import (
    UserCreateStudent,
    UserCreateParent,
    UserResponse,
    UserLogin,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Get current authenticated user from token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


def require_role(allowed_roles: list):
    """Dependency to require specific role(s)."""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {allowed_roles}"
            )
        return current_user
    return role_checker


@router.post("/register/student", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_student(
    user_data: UserCreateStudent,
    db: Session = Depends(get_db)
):
    """Register a new student account."""
    auth_service = AuthService(db)

    # Check for existing username
    if auth_service.get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check for existing email
    if auth_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        user = auth_service.create_student(user_data)
        return UserResponse.model_validate(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )


@router.post("/register/parent", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_parent(
    user_data: UserCreateParent,
    db: Session = Depends(get_db)
):
    """Register a new parent account with student link request."""
    auth_service = AuthService(db)

    # Check for existing username
    if auth_service.get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check for existing email
    if auth_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        user, link = auth_service.create_parent(user_data)
        return {
            "user": UserResponse.model_validate(user),
            "link_status": "pending",
            "message": "Account created. Your link request to the student is pending admin approval."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login with username and password."""
    auth_service = AuthService(db)

    user = auth_service.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user info."""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.post("/password-reset/request")
def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request a password reset token."""
    auth_service = AuthService(db)

    token = auth_service.create_password_reset_token(request.email)

    # Always return success to prevent email enumeration
    # In production, send actual email here
    if token:
        # TODO: Send email with reset link
        # For now, return token for testing
        return {
            "message": "If the email exists, a password reset link has been sent.",
            "token": token  # Remove in production!
        }

    return {
        "message": "If the email exists, a password reset link has been sent."
    }


@router.post("/password-reset/confirm")
def confirm_password_reset(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token."""
    auth_service = AuthService(db)

    success = auth_service.reset_password(data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    return {"message": "Password has been reset successfully"}


@router.post("/password/change")
def change_password(
    data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password (authenticated user)."""
    auth_service = AuthService(db)

    # Verify current password
    user = auth_service.authenticate_user(
        current_user["username"],
        data.current_password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Change password
    success = auth_service.change_password(current_user["user_id"], data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

    return {"message": "Password changed successfully"}
