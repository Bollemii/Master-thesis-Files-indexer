from datetime import datetime, timedelta
from typing import Optional
import uuid
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings
from app.models import User
from app.database.users import get_user_by_username


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a hash from a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def verify_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Verify a JWT token and return the token data."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data


def get_current_user(
    token_data: TokenData = Depends(verify_token)
) -> User:
    """Get the current authenticated user based on the token."""
    user = get_user_by_username(token_data.username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(
        id=uuid.UUID(user.id),
        username=user.username,
        is_superuser=user.is_superuser,
        creation_date=user.creation_date,
        hashed_password=user.hashed_password,
    )


def authenticate_user(username: str, password: str) -> User:
    """Authenticate a user based on username and password."""
    user = get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return User(
        id=uuid.UUID(user.id),
        username=user.username,
        is_superuser=user.is_superuser,
        creation_date=user.creation_date,
        hashed_password=user.hashed_password,
    )


# Helper function to require authentication
require_auth = Security(get_current_user)
