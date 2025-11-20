from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
	email: EmailStr = Field(..., description="Unique email address")
	password: str = Field(..., min_length=6, max_length=128, description="Plain text password")


class UserLogin(BaseModel):
	email: EmailStr
	password: str
