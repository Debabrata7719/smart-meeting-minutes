# 🚀 Quick Streamlit Cloud Deployment

## Prerequisites
1. GitHub account
2. Code pushed to GitHub repository

## Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Ready for Streamlit Cloud"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository
5. Set **Main file path**: `app.py`
6. Click **"Deploy"**

## ⚠️ Important: FFmpeg Issue

**Streamlit Cloud does NOT include ffmpeg by default.**

### Solution Options:

#### Option A: Use `packages.txt` (if supported)
The `packages.txt` file is included - Streamlit Cloud may install it automatically.

#### Option B: Custom Docker Image
Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Option C: Alternative Hosting
Consider Railway, Render, or Fly.io which support Docker/ffmpeg better.

## Files Ready for Deployment

✅ `app.py` - Main Streamlit app
✅ `requirements.txt` - All Python dependencies
✅ `.streamlit/config.toml` - Streamlit configuration
✅ `packages.txt` - System packages (ffmpeg)
✅ `.gitignore` - Properly configured

## First Deployment

- First run will download Vosk models (~40MB for English)
- May take 5-10 minutes
- Check logs in Streamlit Cloud dashboard

## Troubleshooting

**"ffmpeg not found"** → Use Docker or alternative hosting
**"Memory limit"** → Hindi model is large, consider English-only
**"Import errors"** → Check requirements.txt includes all packages

See `DEPLOYMENT.md` for detailed instructions.


