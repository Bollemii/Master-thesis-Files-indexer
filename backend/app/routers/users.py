from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models import User
from app.schemas import UserCreate, UserDetail
from app.utils.security import (
    Token,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from app.database.users import create_user as create_user_db

router = APIRouter()

@router.post(
    "/user/new",
    response_model=UserDetail,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        user = create_user_db(
            username=user.username,
            password=user.password,
        )

        return UserDetail(
            id=uuid.UUID(user.id),
            username=user.username,
            is_superuser=user.is_superuser,
            creation_date=user.creation_date,
        )
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.post("/token", tags=["auth"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    current_user = authenticate_user(form_data.username, form_data.password)
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
