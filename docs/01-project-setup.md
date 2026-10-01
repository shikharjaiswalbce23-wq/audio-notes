# Phase 1 — Project Setup

> **Status:** ✅ Completed

This document covers:
- Created the Next.js frontend (Vanilla CSS) in `/frontend`
- Created the FastAPI backend in `/backend`
- Set up the SQLite database connection as default (easily updatable to PostgreSQL)
- Implemented the `/health` endpoint
- Setup `.env` for backend

---

### How to Run Locally

**Frontend:**
```bash
cd frontend
npm run dev
```
Runs on `http://localhost:3000`.

**Backend:**
```bash
cd backend
# Activate virtual environment
.\venv\Scripts\activate  # Windows
# Run the FastAPI server
uvicorn main:app --reload
```
Runs on `http://localhost:8000`. Test the health endpoint at `http://localhost:8000/health`.
