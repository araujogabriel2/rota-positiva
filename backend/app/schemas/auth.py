from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=256)


class AuthenticatedUser(BaseModel):
    id: str
    email: EmailStr


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = Field(gt=0)
    token_type: Literal["bearer"] = "bearer"
    user: AuthenticatedUser


class ApiError(BaseModel):
    detail: str
