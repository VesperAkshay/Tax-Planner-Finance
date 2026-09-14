"""
Authentication and JWT User Scoping Service (Task 8.7).

Handles:
- User registration and password hashing via bcrypt.
- JWT token generation and validation via python-jose.
- Current user dependency injecting the authenticated User into protected routes.
- Strict user-scoping ensuring multi-tenant isolation.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import get_settings
from app.database import get_db_session
from app.models.account import Account
from app.models.user import User, UserCreate, UserRead

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ==============================================================================
# Security Utilities
# ==============================================================================


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    """
    FastAPI dependency that extracts and validates the JWT from Authorization header
    and retrieves the corresponding active User from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
        user_id = int(user_id_raw)
    except (JWTError, ValueError):
        raise credentials_exception

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# ==============================================================================
# Schemas
# ==============================================================================


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LoginRequest(BaseModel):
    email: str
    password: str


# ==============================================================================
# Endpoints
# ==============================================================================


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    session: Session = Depends(get_db_session),
) -> TokenResponse:
    """Registers a new user, sets up an initial primary account, and issues an access token."""
    existing_user = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A user with email '{user_in.email}' already exists.",
        )

    hashed_pw = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        pan=user_in.pan,
        is_active=user_in.is_active,
        hashed_password=hashed_pw,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Automatically create a primary savings account for the user
    primary_acc = Account(
        user_id=user.id,
        account_name="Primary Savings",
        bank_name="Default Bank",
        account_type="savings",
        currency="INR",
        current_balance=0.0,
    )
    session.add(primary_acc)
    session.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    session: Session = Depends(get_db_session),
) -> TokenResponse:
    """Authenticates a user with email and password and returns a JWT access token."""
    user = session.exec(select(User).where(User.email == credentials.email)).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account.")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Returns the authenticated user's profile."""
    return UserRead.model_validate(current_user)
