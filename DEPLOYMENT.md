# 🚀 Streamlit Cloud Deployment Guide

This guide will help you deploy Smart Meeting Minutes to Streamlit Cloud.

## Prerequisites

1. **GitHub Account** - You need a GitHub account
2. **GitHub Repository** - Your project must be in a GitHub repository
3. **Streamlit Cloud Account** - Sign up at [share.streamlit.io](https://share.streamlit.io)

## Step 1: Push to GitHub

1. Initialize git repository (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Smart Meeting Minutes"
   ```

2. Create a new repository on GitHub (or use existing)

3. Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Fill in the details:
   - **Repository**: Select your repository
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `app.py`
5. Click **"Deploy"**

## Step 3: Important Notes

### ⚠️ FFmpeg Requirement

**Streamlit Cloud does NOT have ffmpeg installed by default.**

You have two options:

#### Option 1: Use Streamlit Community Cloud (Limited)
- The app will work but audio conversion will fail
- You'll need to upload pre-converted WAV files
- Or use a different hosting service

#### Option 2: Use Custom Docker Image (Recommended)
Create a `Dockerfile` in your repository:

```dockerfile
FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Then in Streamlit Cloud settings, enable "Use custom Docker image" and specify your Docker image.

### Alternative: Use pydub (Python-only solution)

If you want to avoid ffmpeg dependency, you can modify the code to use `pydub` with `simpleaudio` or other Python libraries, but this may have limitations.

## Step 4: Environment Variables (Optional)

If you need any environment variables, add them in Streamlit Cloud:
1. Go to your app settings
2. Click "Secrets"
3. Add your secrets in TOML format

## Step 5: Monitor Deployment

- Check the logs in Streamlit Cloud dashboard
- First deployment may take 5-10 minutes (downloading models)
- Vosk models will be downloaded automatically on first use

## Troubleshooting

### Issue: "ffmpeg not found"
**Solution**: Streamlit Cloud doesn't have ffmpeg. You need to:
- Use a custom Docker image with ffmpeg
- Or modify code to use Python-only audio libraries
- Or use a different hosting service (Heroku, Railway, etc.)

### Issue: "Model download timeout"
**Solution**: Models are large. First run may take time. Be patient.

### Issue: "Memory limit exceeded"
**Solution**: 
- Streamlit Community Cloud has ~1GB RAM limit
- Hindi model is ~1.5GB - may not fit
- Consider using only English model for cloud deployment

### Issue: "Import errors"
**Solution**: 
- Ensure all dependencies are in `requirements.txt`
- Check that `app.py` is in the root directory
- Verify Python path setup in `app.py`

## Recommended Hosting Alternatives

If Streamlit Cloud doesn't work due to ffmpeg:

1. **Railway** - Easy deployment, supports Docker
2. **Render** - Free tier available
3. **Heroku** - Classic platform (paid now)
4. **Fly.io** - Good for Docker deployments
5. **DigitalOcean App Platform** - Simple deployments

All of these support Docker and can have ffmpeg installed.

## Success Checklist

- ✅ Code pushed to GitHub
- ✅ Repository is public (or you have Streamlit Cloud Pro)
- ✅ `app.py` is in root directory
- ✅ `requirements.txt` includes all dependencies
- ✅ `.streamlit/config.toml` is configured
- ✅ FFmpeg issue addressed (Docker or alternative)

---

**Need help?** Check Streamlit Cloud documentation or open an issue in the repository.


