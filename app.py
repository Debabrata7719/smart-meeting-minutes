from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.routes import router as auth_router
from auth.routes import get_current_user
from ai.routes import router as ai_router


app = FastAPI(title="Smart Meeting Minutes API", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(ai_router, prefix="/ai")


@app.get("/")
def root() -> dict[str, str]:
	return {"status": "ok", "message": "Smart Meeting Minutes API"}


@app.get("/test")
def test_backend() -> dict[str, str]:
	return {"message": "Backend is running"}


@app.get("/test-protected")
def test_protected(current_user: str = Depends(get_current_user)) -> dict[str, str]:
	return {
		"message": "Authorized access",
		"user_id": current_user,
	}