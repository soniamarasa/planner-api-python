from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import (
    LoginResponse,
    MessageResponse,
    RecoverPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.mail import send_email

router = APIRouter()


@router.post("/createAccount", response_model=UserResponse)
def create_account(payload: UserCreate, db: Session = Depends(get_db_session)) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists.")

    user = User(
        name=payload.name,
        email=payload.email,
        password=get_password_hash(payload.password),
        birthdate=payload.birthdate,
        gender=payload.gender,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
def login(payload: UserLogin, db: Session = Depends(get_db_session)) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist.")

    if not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password.")

    token = create_access_token(str(user.id))
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "gender": user.gender,
            "birthdate": user.birthdate,
            "token": token,
        }
    }


@router.post("/logout")
def logout() -> dict:
    return {"user": None}


@router.post("/retrievePassword", response_model=MessageResponse)
def recover_password(payload: RecoverPasswordRequest, db: Session = Depends(get_db_session)) -> MessageResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist.")

    token = create_access_token(str(user.id), expires_in="2h")
    link = f"{payload.host}/password-reset/{token}"
    send_email(user.email, user.name, "Reset your password", link)
    return MessageResponse(message="The link to reset a new password has been sent to your email.")


@router.post("/resetPassword", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> MessageResponse:
    current_user.password = get_password_hash(payload.password)
    db.add(current_user)
    db.commit()
    return MessageResponse(message="Password changed successfully!")


@router.get("/user/{user_id}", response_model=UserResponse)
def get_user(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db_session)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this user.")
    return user


@router.put("/updateUser/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist.")
    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this user.")

    if payload.email and payload.email != user.email:
        existing_email = db.scalar(select(User).where(User.email == payload.email))
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail already registered!")
        user.email = payload.email

    if payload.oldPassword:
        if not verify_password(payload.oldPassword, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password.")

    if payload.password:
        if payload.password != payload.confirmPassword:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match.")
        user.password = get_password_hash(payload.password)

    if payload.name is not None:
        user.name = payload.name
    if payload.birthdate is not None:
        user.birthdate = payload.birthdate
    if payload.gender is not None:
        user.gender = payload.gender

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
