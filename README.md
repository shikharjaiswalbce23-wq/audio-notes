# 🎙️ Audio Notes Platform

A web application that lets users upload audio files and automatically get a **transcript** and **AI-generated summary** — powered by Gnan.ai speech-to-text and an LLM API.

---

## 📋 Project Overview

Users upload an audio recording. The application:
1. Stores the audio file in cloud object storage.
2. Sends the audio to **Gnan.ai ASR** for transcription (in the background).
3. Sends the transcript to an **LLM** for summarization (in the background).
4. Shows live status, transcript, and summary to the user.

The UI never freezes — background jobs handle the heavy work.

---

## ✨ Features

- Upload audio files (MP3, WAV, M4A, etc.)
- Background transcription via Gnan.ai ASR
- AI-generated summary of the transcript
- Live progress tracking (polling-based)
- Clear error messages if anything fails
- All secrets kept server-side

---

## 🏗️ Architecture

```
Next.js Frontend
      ↓ HTTP
FastAPI Backend
      ↓              ↓
PostgreSQL       S3 Storage
      ↓
    Redis
      ↓
  RQ Worker
   ↓       ↓
Gnan.ai   LLM API
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full diagram.

---

## 🛠️ Technology Stack

| Layer          | Technology          |
|----------------|---------------------|
| Frontend       | Next.js (JavaScript)|
| Backend        | FastAPI (Python)    |
| Database       | PostgreSQL          |
| Object Storage | S3-compatible (R2 / AWS S3) |
| Job Queue      | Redis + RQ          |
| Transcription  | Gnan.ai ASR API     |
| Summarization  | LLM API (OpenAI / Gemini) |
| Deployment     | Vercel + Render/Railway |

---

## 📁 Folder Structure

> Will be filled in as phases are completed.

```
audio-notes/
├── frontend/        # Next.js app
├── backend/         # FastAPI + RQ worker
├── docs/            # All documentation
├── .gitignore
├── README.md
└── .env.example
```

---

## 🚀 Local Setup

> Will be filled in as phases are completed.

---

## 🔑 Environment Variables

> See `backend/.env.example` and `frontend/.env.example` — filled in as phases are completed.

**Never commit real API keys.**

---

## 📦 Running Services

> Will be filled in as phases are completed.

---

## 📡 API Endpoints

> See [docs/API.md](docs/API.md)

---

## 🔄 Background Processing

> See [docs/05-background-jobs.md](docs/05-background-jobs.md)

---

## 🎙️ Gnan.ai Integration

> See [docs/06-gnan-transcription.md](docs/06-gnan-transcription.md)

---

## 🤖 LLM Summarization

> See [docs/07-summarization.md](docs/07-summarization.md)

---

## 🌐 Deployment

> See [docs/11-deployment.md](docs/11-deployment.md)

---

## 🐛 Troubleshooting

> See [docs/troubleshooting.md](docs/troubleshooting.md)

---

## 🔮 Future Improvements

- Speaker diarization (identify who is speaking)
- Multiple file formats / batch uploads
- User authentication
- Export summary as PDF
- Real-time transcription via WebSockets

---

## 📄 License

MIT
