from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(student|parent|admin)$")


class UserCreateStudent(UserBase):
    """Student self-registration."""
    password: str = Field(..., min_length=8)


class UserCreateParent(UserBase):
    """Parent self-registration with student link request."""
    password: str = Field(..., min_length=8)
    student_email_or_username: str = Field(..., description="Email or username of the student to link with")


class UserUpdate(BaseModel):
    """User update schema (admin only)."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login credentials."""
    username: str
    password: str


class PasswordResetRequest(BaseModel):
    """Request password reset."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordChange(BaseModel):
    """Change password (authenticated user)."""
    current_password: str
    new_password: str = Field(..., min_length=8)
