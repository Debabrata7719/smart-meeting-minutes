# 🎙️ Smart Meeting Minutes

An intelligent offline tool that transforms meeting recordings into structured summaries and actionable highlights. No API keys required - everything runs locally on your machine.

## ✨ Features

- **Offline Transcription**: Uses Vosk for speech-to-text conversion (no internet required)
- **AI-Powered Summarization**: Generates concise meeting summaries using Hugging Face Transformers
- **Smart Highlights Extraction**: Automatically identifies and categorizes important topics, decisions, and action items
- **Multi-language Support**: Transcribe English or Hindi audio
- **Context-Aware Extraction**: Captures full context around important statements, not just keywords
- **Efficient Processing**: Streaming transcription with real-time progress tracking

## 📋 Requirements

- Python 3.8+
- ffmpeg (for audio processing)
- Required Python packages (see `requirements.txt`)

### Installing Dependencies

```bash
# Install Python packages (includes Streamlit)
pip install -r requirements.txt

# For summarization (optional but recommended)
pip install transformers torch

# Install ffmpeg
# Windows: winget install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg
```

**Note:** Streamlit is included in `requirements.txt` for the web interface.

## 🚀 Quick Start

### Web Interface (Recommended)

Launch the Streamlit web interface for an easy-to-use GUI:

```bash
streamlit run app.py
```

This will open your browser automatically. You can:
- Upload audio/video files via drag-and-drop
- Select language and options
- View results in the browser
- Download summary and highlights files

### Command Line Interface

Alternatively, use the command-line interface:

```bash
# Process a meeting audio/video file
python -m src.transcripter.cli "path/to/meeting.mp4"
```

This will generate:
- `meeting_summary.txt` - Concise summary of the meeting
- `meeting_highlights.txt` - Structured highlights with categorized important topics

### Advanced CLI Usage

```bash
# Hindi transcription with English translation
python -m src.transcripter.cli meeting.mp3 --language hi --translate

# Skip summarization (only generate highlights)
python -m src.transcripter.cli meeting.mp3 --skip-summary

# Custom output directory
python -m src.transcripter.cli meeting.mp3 --outdir my_outputs

# Disable progress updates
python -m src.transcripter.cli meeting.mp3 --no-progress
```

## 📂 Output Files

### `{filename}_summary.txt`
A concise, AI-generated summary of the entire meeting. Perfect for quick overviews.

### `{filename}_highlights.txt`
Well-structured highlights organized by categories:

- **Key Decisions & Actions**: Important decisions, agreements, and action items
- **Financial Metrics**: Revenue, profit, costs, budgets, pricing
- **Growth & Business**: Market expansion, sales, deals, contracts
- **Customer & Users**: Customer metrics, retention, churn
- **Planning & Forecasting**: Forecasts and future planning
- **Operations & Team**: Hiring, headcount, team updates

Each highlight includes full context, making it easy to understand what was discussed.

## 🛠️ How It Works

1. **Audio Processing**: Converts input audio/video to mono 16kHz WAV format using ffmpeg
2. **Transcription**: Uses Vosk offline speech recognition model to convert speech to text
3. **Analysis**: Extracts important topics using intelligent pattern matching and context detection
4. **Summarization**: Generates concise summary using Hugging Face Transformers models
5. **Structuring**: Organizes highlights into categorized, readable format

## 🌍 Language Support

- **English** (default): Full support for transcription and summarization
- **Hindi**: Transcription support with optional English translation

### Language Examples

```bash
# English (default)
python -m src.transcripter.cli meeting.mp3

# Hindi transcription
python -m src.transcripter.cli meeting.mp3 --language hi

# Hindi with English translation
python -m src.transcripter.cli meeting.mp3 --language hi --translate
```

## 📝 Command Line Options

```
positional arguments:
  input                 Path to input audio file (.mp3/.wav/.mp4/etc)

optional arguments:
  --outdir OUTDIR       Directory to write output files (default: outputs)
  --skip-summary        Skip summarization, only generate highlights
  --language {en,hi}    Language of the audio (default: en)
  --translate           Translate Hindi transcript to English
  --no-streaming        Disable streaming transcription
  --no-progress         Disable progress updates
  --timestamps          Include timestamps in processing (for internal use)
  --reuse-transcript    Use existing transcript file instead of audio
  --important-only      Extract only sentences with important keywords
```

## 🎯 Use Cases

- **Team Meetings**: Quickly capture decisions and action items
- **Client Calls**: Generate summaries for follow-up
- **Conference Calls**: Extract key points from long discussions
- **Interviews**: Summarize important responses and topics
- **Training Sessions**: Create structured notes from recordings

## 🔧 Technical Details

### Core Technologies

- **ffmpeg**: Audio/video preprocessing and format conversion
- **Vosk**: Offline speech-to-text recognition
- **Hugging Face Transformers**: Text summarization and translation
- **Python 3.8+**: Core runtime

### Model Downloads

Vosk models are automatically downloaded on first use:
- English: `vosk-model-small-en-us-0.15` (~40MB)
- Hindi: `vosk-model-hi-0.22` (~1.5GB)

Models are cached in the `models/` directory for future use.

## 📊 Example Output

### Summary (`meeting_summary.txt`)
```
The meeting discussed quarterly performance metrics, with revenue 
increasing by 15%. The team agreed to expand into new markets 
and approved a budget increase of 20% for next quarter...
```

### Highlights (`meeting_highlights.txt`)
```
======================================================================
MEETING HIGHLIGHTS
======================================================================

KEY DECISIONS & ACTIONS
----------------------------------------------------------------------
  1. We decided to increase the budget by 20% for next quarter. The team agreed this is necessary for expansion.
  2. We will launch the new product next month. Marketing needs to prepare the campaign by next week.

FINANCIAL METRICS
----------------------------------------------------------------------
  1. Revenue increased by 15% this quarter compared to last year.
  2. We need to review the budget allocation for the upcoming projects.

GROWTH & BUSINESS
----------------------------------------------------------------------
  1. The new market expansion plan is ready for implementation.
  2. We closed three major deals this month worth $500k total.

======================================================================
Total Highlights: 6
======================================================================
```

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📄 License

This project is open source and available for personal and commercial use.

## ⚠️ Notes

- First run will download Vosk models (may take a few minutes)
- Summarization requires `transformers` and `torch` packages
- Large audio files may take time to process
- All processing happens offline - no data is sent to external services

---


