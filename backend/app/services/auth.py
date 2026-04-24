import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models import User, UserRole, PasswordResetToken, ParentStudentLink, LinkStatus
from app.schemas.auth import UserCreate, UserCreateStudent, UserCreateParent, PasswordResetConfirm


# Password hashing using PBKDF2 (built-in, no extra deps)
def hash_password(password: str) -> str:
    """Hash a password using PBKDF2."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + pwdhash.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    salt = hashed_password[:32]
    stored_hash = hashed_password[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
    return pwdhash.hex() == stored_hash


# JWT handling (using simple implementation with secrets)
def create_access_token(user_id: int, username: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a simple token (in production, use proper JWT library)."""
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    expire = datetime.utcnow() + expires_delta
    # Simple token format: user_id:username:role:expire:signature
    token_data = f"{user_id}:{username}:{role}:{int(expire.timestamp())}"
    signature = hashlib.sha256((token_data + secrets.token_hex(32)).encode()).hexdigest()[:16]
    return f"{token_data}:{signature}"


def decode_token(token: str) -> Optional[dict]:
    """Decode a token. Returns None if invalid."""
    try:
        parts = token.split(":")
        if len(parts) != 5:
            return None

        user_id, username, role, expire_timestamp, signature = parts
        expire = datetime.fromtimestamp(int(expire_timestamp))

        if datetime.utcnow() > expire:
            return None

        return {
            "user_id": int(user_id),
            "username": username,
            "role": role,
            "exp": expire
        }
    except (ValueError, IndexError):
        return None


class AuthService:
    """Authentication service for user management."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user (admin only)."""
        hashed_password = hash_password(user_data.password)

        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=UserRole(user_data.role),
            full_name=user_data.full_name,
            is_active=True
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_student(self, user_data: UserCreateStudent) -> User:
        """Create a new student account (self-registration)."""
        hashed_password = hash_password(user_data.password)

        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=UserRole.STUDENT,
            full_name=user_data.full_name,
            is_active=True
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_parent(self, user_data: UserCreateParent) -> tuple[User, Optional[ParentStudentLink]]:
        """Create a new parent account with student link request."""
        # Find student by email or username
        student = self.get_user_by_email(user_data.student_email_or_username)
        if not student:
            student = self.get_user_by_username(user_data.student_email_or_username)

        if not student or student.role != UserRole.STUDENT:
            raise ValueError("Student not found with the provided email or username")

        hashed_password = hash_password(user_data.password)

        parent = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=UserRole.PARENT,
            full_name=user_data.full_name,
            is_active=True
        )

        self.db.add(parent)
        self.db.flush()  # Get the parent ID

        # Create pending link
        link = ParentStudentLink(
            parent_id=parent.id,
            student_id=student.id,
            status=LinkStatus.PENDING,
            requested_at=datetime.utcnow()
        )

        self.db.add(link)
        self.db.commit()
        self.db.refresh(parent)
        self.db.refresh(link)

        return parent, link

    def update_user(self, user_id: int, **updates) -> Optional[User]:
        """Update user fields."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        for field, value in updates.items():
            if hasattr(user, field):
                setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        user.hashed_password = hash_password(new_password)
        self.db.commit()
        return True

    def create_password_reset_token(self, email: str) -> Optional[str]:
        """Create a password reset token for user."""
        user = self.get_user_by_email(email)
        if not user:
            return None

        # Generate random token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )

        self.db.add(reset_token)
        self.db.commit()

        return token

    def verify_reset_token(self, token: str) -> Optional[int]:
        """Verify reset token and return user_id if valid."""
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()

        if not reset_token:
            return None

        return reset_token.user_id

    def reset_password(self, data: PasswordResetConfirm) -> bool:
        """Reset password using token."""
        user_id = self.verify_reset_token(data.token)
        if not user_id:
            return False

        # Update password
        if not self.change_password(user_id, data.new_password):
            return False

        # Mark token as used
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == data.token
        ).first()

        if reset_token:
            reset_token.used_at = datetime.utcnow()
            self.db.commit()

        return True
