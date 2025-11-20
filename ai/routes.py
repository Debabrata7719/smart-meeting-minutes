from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from auth.routes import get_current_user
from .summarizer import SummarizationError, summarize_text
from .transcriber import TranscriptionError, transcribe_audio


router = APIRouter(prefix="", tags=["ai"])

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".mp3", ".wav"}


def _ensure_upload_dir() -> None:
	UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


_ensure_upload_dir()


@router.get("/check")
def check_ai_routes(_: str = Depends(get_current_user)) -> dict[str, str]:
	return {"message": "AI routes active"}


@router.get("/test", summary="AI backend heartbeat")
def ai_test(_: str = Depends(get_current_user)) -> dict[str, str]:
	return {"message": "AI backend working"}


@router.post(
	"/upload",
	summary="Upload audio and receive transcript + summary",
	responses={
		200: {
			"description": "Transcription + summary generated",
			"content": {
				"application/json": {
					"example": {
						"transcript": "hello everyone welcome to the meeting",
						"summary": "The speaker greeted the team and opened the meeting.",
					}
				}
			},
		}
	},
)
async def upload_audio(
	file: UploadFile = File(...),
	_: str = Depends(get_current_user),
) -> dict[str, str]:
	if not file:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="No audio file provided. Attach a .mp3 or .wav file.",
		)

	extension = Path(file.filename or "").suffix.lower()
	if extension not in ALLOWED_EXTENSIONS:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Only .mp3 and .wav audio formats are supported.",
		)

	_ensure_upload_dir()
	dest_path = UPLOAD_DIR / f"{uuid4().hex}{extension}"
	print(f"[AI] Upload received: {file.filename} -> {dest_path}")
	try:
		with dest_path.open("wb") as buffer:
			shutil.copyfileobj(file.file, buffer)
	finally:
		await file.close()

	try:
		print(f"[AI] Starting transcription for {dest_path.name}")
		transcript = transcribe_audio(dest_path)
		print(f"[AI] Finished transcription for {dest_path.name}")
	except FileNotFoundError:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Uploaded file could not be processed.",
		)
	except (TranscriptionError, ValueError) as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		) from exc

	if not transcript:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="No transcript could be generated from the audio.",
		)

	try:
		print(f"[AI] Starting summary for {dest_path.name}")
		summary = summarize_text(transcript)
		print(f"[AI] Finished summary for {dest_path.name}")
	except SummarizationError as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc

	return {
		"transcript": transcript,
		"summary": summary,
	}

