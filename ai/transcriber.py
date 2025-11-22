from __future__ import annotations

import os
import wave
from functools import lru_cache
from pathlib import Path

from vosk import KaldiRecognizer, Model

# Path to Vosk model
MODEL_PATH = Path(
    os.environ.get("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15")
)


class TranscriptionError(RuntimeError):
    """Raised when audio transcription fails."""


def _ensure_model_path() -> Path:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Vosk model not found at '{MODEL_PATH}'. "
            "Download a model and update VOSK_MODEL_PATH if necessary."
        )
    return MODEL_PATH


@lru_cache(maxsize=1)
def _load_model() -> Model:
    model_path = _ensure_model_path()
    return Model(str(model_path))


def transcribe_audio(file_path: str | Path) -> str:
    """
    Transcribe a local audio file (.wav only) using a local Vosk model.
    Render-compatible version (no ffmpeg/pydub).
    """

    source_path = Path(file_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Audio file not found: {source_path}")

    # 🚫 No MP3 supported on Render
    if source_path.suffix.lower() != ".wav":
        raise TranscriptionError("Only .wav files are supported on the server.")

    model = _load_model()

    # Read WAV directly
    with wave.open(str(source_path), "rb") as wf:
        # Must be 16kHz mono PCM 16-bit
        if (
            wf.getnchannels() != 1
            or wf.getframerate() != 16000
            or wf.getsampwidth() != 2
        ):
            raise TranscriptionError(
                "WAV file must be 16-bit PCM, mono, 16kHz."
            )

        return _run_recognizer(model, wf)


def _run_recognizer(model: Model, wf: wave.Wave_read) -> str:
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    transcript_parts = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            text = _extract_text(rec.Result())
            if text:
                transcript_parts.append(text)

    final_text = _extract_text(rec.FinalResult())
    if final_text:
        transcript_parts.append(final_text)

    return " ".join(part.strip() for part in transcript_parts if part.strip()).strip()


def _extract_text(result: str) -> str:
    import json

    try:
        data = json.loads(result)
        return data.get("text", "")
    except json.JSONDecodeError:
        return ""
