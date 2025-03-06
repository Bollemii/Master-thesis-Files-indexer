from datetime import datetime, timedelta
from typing import Annotated, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlmodel import Session, select
from app.models import User
from app.database import get_session

# Configuration
SECRET_KEY = "740b6ea71528914a03a0404f5a9573236410dd68b4c00de3913575b4aed9a924"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SessionDep = Annotated[Session, Depends(get_session)]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Verify a JWT token and return the token data."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data


def get_current_user(
    session: SessionDep, token_data: TokenData = Depends(verify_token)
) -> User:
    """Get the current authenticated user based on the token."""
    user = session.exec(
        select(User).where(User.username == token_data.username)
    ).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def authenticate_user(session: Session, username: str, password: str) -> User:
    """Authenticate a user based on username and password."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# def create_user(session: Session, user: User) -> User:

# Helper function to require authentication
require_auth = Security(get_current_user)
