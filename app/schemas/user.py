from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    birthdate: date | None = None
    gender: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    birthdate: date | None = None
    gender: str | None = None
    oldPassword: str | None = Field(default=None, min_length=6)
    password: str | None = Field(default=None, min_length=6)
    confirmPassword: str | None = None


class RecoverPasswordRequest(BaseModel):
    email: EmailStr
    host: str


class ResetPasswordRequest(BaseModel):
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    birthdate: date | None
    gender: str | None


class AuthenticatedUser(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    birthdate: date | None
    gender: str | None
    token: str


class LoginResponse(BaseModel):
    user: AuthenticatedUser


class MessageResponse(BaseModel):
    message: str
