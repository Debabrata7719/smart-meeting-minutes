# 🎙️ Smart Meeting Minutes API

FastAPI backend for processing meeting recordings, managing users, and serving protected resources via JWT authentication.

## ✨ Features

- Offline transcription powered by Vosk and custom NLP utilities (see `src/transcripter/`).
- Manual authentication system backed by MongoDB + bcrypt + jose JWT tokens.
- Modular `auth/` package that cleanly separates database access, hashing, token utilities, and routes.
- Protected routes using the `Authorization` header (`Authorization: <token>` or `Authorization: Bearer <token>`).

## 📦 Requirements

- Python 3.10+
- Local MongoDB running at `mongodb://localhost:27017`
- ffmpeg (for the transcription utilities)
- Python dependencies listed in `requirements.txt`

Install everything with:

```bash
pip install -r requirements.txt
```

## 🚀 Running the API

```bash
uvicorn app:app --reload
# or use the helper scripts
./run.sh            # macOS/Linux
run.bat             # Windows
```

The server starts on `http://127.0.0.1:8000` by default.

## 🔐 Authentication Endpoints

All auth endpoints live under `/auth`:

| Method | Route             | Description                            |
|--------|------------------|----------------------------------------|
| POST   | `/auth/register` | Create a new user (email + password)   |
| POST   | `/auth/login`    | Verify credentials, returns JWT token  |
| GET    | `/auth/profile`  | Requires token, returns current user id |

Usage example (with `httpie`):

```bash
# Register
http POST :8000/auth/register email=jane@example.com password=SuperSecret123

# Login
http POST :8000/auth/login email=jane@example.com password=SuperSecret123
# => {"access_token": "...", "token_type": "bearer"}

# Access profile
http GET :8000/auth/profile "Authorization: <token>"
```

## 🔒 Test Protected Route

The root FastAPI app also exposes `/test-protected` to verify JWT handling:

```bash
http GET :8000/test-protected "Authorization: <token>"
# => {"message": "Authorized access", "user_id": "<mongodb id>"}
```

## 🧠 AI Routes (Transcription + Summaries)

Protected endpoints under `/ai` provide offline transcription and summarization:

| Method | Route         | Description                                  |
|--------|---------------|----------------------------------------------|
| GET    | `/ai/check`   | Quick health-check (requires JWT)            |
| POST   | `/ai/upload`  | Upload mp3/wav, returns transcript+summary   |

Example:

```bash
http POST :8000/ai/upload \
  "Authorization: <token>" \
  file@sample.mp3
```

Responses include both the raw transcript (from the local Vosk model) and a summary generated with `t5-small`.

## 🧱 Project Structure

```
app.py                # FastAPI application entry-point
auth/
  ├─ database.py      # MongoDB client + collections
  ├─ hash.py          # bcrypt helpers
  ├─ models.py        # Pydantic request models
  ├─ routes.py        # Auth router (register/login/profile)
  └─ token.py         # JWT creation/verification
ai/
  ├─ transcriber.py   # Local Vosk-based transcription helpers
  ├─ summarizer.py    # Local Hugging Face summarization helpers
  └─ routes.py        # Protected upload/check endpoints
src/transcripter/     # Existing transcription & NLP utilities
```

## 🧠 Transcription Utilities

The CLI pipeline for transcription/summarization remains available:

```bash
python -m src.transcripter.cli path/to/audio.mp3 --outdir outputs
```

Refer to the module docstrings under `src/transcripter/` for full details on highlights, summaries, PDF export, and translations.

## 🧪 Verify Setup

1. Start MongoDB locally (`brew services start mongodb-community` or similar).
2. Install dependencies (`pip install -r requirements.txt`).
3. Run the API (`uvicorn app:app --reload`).
4. Exercise the auth routes with any HTTP client (curl, httpie, Postman).

## 🤝 Contributing

Contributions are welcome! Please open an issue or PR with improvement ideas.

## 📄 License

This project is open source and free for personal or commercial use.
