from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt


SECRET_KEY = "your_secret_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_token(user_id: str, expires_delta: timedelta | None = None) -> str:
	if expires_delta is None:
		expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

	expire = datetime.now(timezone.utc) + expires_delta
	payload: dict[str, Any] = {"sub": user_id, "exp": expire}
	return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		user_id: str | None = payload.get("sub")
		if not user_id:
			raise JWTError("Token missing subject")
		return user_id
	except JWTError as exc:
		raise ValueError("Invalid or expired token") from exc
