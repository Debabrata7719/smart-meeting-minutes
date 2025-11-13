import subprocess
import shutil
import sys
from pathlib import Path


def ensure_ffmpeg_available() -> None:
    """Raise RuntimeError if ffmpeg is not available in PATH."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found. Install it and ensure it's in PATH. Windows: get it via winget or choco."
        )


def convert_to_wav_mono_16k(input_path: str, output_dir: str | Path) -> Path:
    """
    Convert an input audio file to mono WAV 16kHz PCM (s16le).

    Returns path to the converted file.
    """
    ensure_ffmpeg_available()

    in_path = Path(input_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input audio not found: {in_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{in_path.stem}_audio_16k.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(in_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        "-acodec",
        "pcm_s16le",
        str(out_path),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr.decode(errors="ignore"))
        raise RuntimeError("ffmpeg conversion failed") from exc

    if not out_path.exists():
        raise RuntimeError("Converted file was not created")

    return out_path
