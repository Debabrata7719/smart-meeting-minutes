🎙️ Meeting Transcription & Summarization

This project is designed to transform raw meeting recordings into clear, structured notes without using any paid APIs.

🔎 What It Does

Full Meeting Transcription

Takes an audio/video file as input (e.g., .mp3, .wav).

Converts it into the right format (mono, 16kHz WAV).

Transcribes the entire meeting speech to text using the offline Vosk model.

Meeting Summarization

Once transcription is complete, the text is passed to an open-source summarizer.

Produces a clean, concise summary of the whole meeting.

Scanning for Key Points

The transcript is further scanned to extract highlights and important-only notes.

This ensures the final output is not just text-heavy but also action-oriented.

📂 Outputs Generated

For a meeting file (say meeting.mp3), the system produces:

meeting_transcript.txt → Full transcript of the meeting.

meeting_summary.txt → Short, human-readable summary.

meeting_highlights.txt → Key highlights (optional).

meeting_important.txt → Only the most important points (optional with --important-only).

🚀 Why This Project?

Meetings are often long and repetitive.

This tool saves time by:
✅ Converting speech to text
✅ Summarizing automatically
✅ Highlighting only what matters most

🛠️ Core Technologies

ffmpeg → Audio preprocessing

Vosk → Offline transcription

Hugging Face Transformers → Text summarization