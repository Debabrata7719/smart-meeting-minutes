from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.collection import Collection

from .database import users_collection
from .hash import hash_password, verify_password
from .models import User, UserLogin
from .token import create_token, decode_token

router = APIRouter(prefix="", tags=["auth"])

bearer_scheme = HTTPBearer(auto_error=False)


def get_users_collection() -> Collection:
	return users_collection


def _extract_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
	token = credentials.credentials if credentials else None
	if not token:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Authorization token missing. Click 'Authorize' in Swagger and paste your JWT.",
		)
	return token


def get_current_user(token: str = Depends(_extract_token)) -> str:
	try:
		user_id = decode_token(token)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

	if not ObjectId.is_valid(user_id):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id in token.")

	user = users_collection.find_one({"_id": ObjectId(user_id)})
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or deleted.")
	return str(user["_id"])


@router.post(
	"/register",
	summary="Create a new account",
	status_code=status.HTTP_201_CREATED,
)
def register(user: User, collection: Collection = Depends(get_users_collection)) -> dict[str, str]:
	email = user.email.lower()
	if collection.find_one({"email": email}):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="User already exists. Please log in instead.",
		)

	hashed_password = hash_password(user.password)
	result = collection.insert_one({"email": email, "password": hashed_password})
	return {
		"message": "User registered successfully",
		"user_id": str(result.inserted_id),
	}


@router.post(
	"/login",
	summary="Log in and get JWT",
	responses={
		200: {
			"description": "Login successful",
			"content": {
				"application/json": {
					"example": {
						"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
						"token_type": "bearer",
					}
				}
			},
		},
	},
)
def login(credentials: UserLogin, collection: Collection = Depends(get_users_collection)) -> dict[str, str]:
	email = credentials.email.lower()
	user = collection.find_one({"email": email})
	if not user or not verify_password(credentials.password, user.get("password", "")):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid email or password. Please try again.",
		)

	token = create_token(str(user["_id"]))
	return {"access_token": token, "token_type": "bearer"}


@router.get("/profile")
def profile(current_user: str = Depends(get_current_user)) -> dict[str, str]:
	return {"user_id": current_user}


@router.get("/test-protected", summary="Verify auth works", tags=["auth"])
def auth_test_protected(current_user: str = Depends(get_current_user)) -> dict[str, str]:
	return {"message": "You are authorized", "user_id": current_user}
