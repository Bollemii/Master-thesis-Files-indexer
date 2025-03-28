# Router for user related operations
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.database import get_session
from app.models import User
from app.schemas import UserDetail, UserCreate
from app.utils.security import (
    Token,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


@router.post(
    "/user/new",
    response_model=UserDetail,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
async def create_user(user: UserCreate, session: SessionDep):
    """Create a new user"""
    try:
        user = User(
            **user.model_dump(), hashed_password=get_password_hash(user.password)
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token", tags=["auth"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> Token:
    current_user = authenticate_user(session, form_data.username, form_data.password)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": current_user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/user/me",
    response_model=UserDetail,
    status_code=status.HTTP_200_OK,
    tags=["users"],
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Retrieve the current user"""
    return current_user
