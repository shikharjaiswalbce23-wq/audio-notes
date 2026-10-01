# Phase 10 — Testing

> **Status:** ✅ Implemented

## Goal
To ensure the backend logic is robust through automated unit tests and to define a manual end-to-end test plan for verifying the entire pipeline (including failure cases) across the frontend and backend.

---

## What was implemented

### 1. API Endpoint Tests (`test_phase10_api.py`)
Tested the FastAPI routing and HTTP response layer.
- Uses `fastapi.testclient.TestClient` and an in-memory SQLite database.
- Verifies successful uploads return a `201` status and the correct JSON schema.
- Verifies invalid files (e.g., PDFs) are rejected with a `400` status.
- Validates the `/uploads/:id` endpoint returns `404` for unknown IDs and correctly reflects processing state changes.
- Tests that unhandled exceptions trigger the global `500` error handler and don't leak internal details.

### 2. CRUD Layer Tests (`test_phase10_crud.py`)
Tested database persistence and interactions.
- Validates that `create_upload` generates unique UUIDs and correct initial state.
- Ensures `update_upload_status` safely handles `None` progress updates and correctly sets error messages.
- Verifies the full pipeline progression (`UPLOADING` -> `QUEUED` -> `TRANSCRIBING` -> `SUMMARIZING` -> `COMPLETED`).
- Confirms `update_upload_results` correctly stores transcripts and AI summaries without overwriting each other.

### 3. Worker Pipeline Tests (`test_phase10_worker.py`)
Tested the Redis worker logic (`tasks.py`) independently of external APIs.
- Mocks all external calls (storage, Gnan.ai STT, Gemini LLM).
- Verifies the "happy path" persists transcripts, summaries, and hits all progress milestones (10, 30, 70, 75, 90, 100).
- Validates failure sanitization: Confirms that `RuntimeError`s from storage or APIs are caught, and only safe, user-friendly strings (e.g., "speech-to-text service unavailable") are saved to the database.
- Ensures stack traces are never exposed to the `error_message` column.
- Validates correct status transition ordering (e.g., `TRANSCRIBING` is set before calling the STT service).

---

## End-to-End Manual Test Plan

To verify the system fully works from the user's browser down to the external APIs, perform the following manual tests:

### 1. Happy Path
1. Start the backend (`uvicorn main:app`), Redis worker (`rq worker`), and frontend (`npm run dev`).
2. Open `http://localhost:3000` and upload a valid audio file (MP3/WAV).
3. **Verify:** The UI transitions from Uploading -> Queued -> Transcribing -> Summarizing -> Completed. The final transcript and summary are displayed correctly.

### 2. Failure Cases
- **Invalid File Type:** Try to upload a `.txt` or `.pdf` file. 
  - **Verify:** The frontend rejects it, or the API returns a 400 error immediately.
- **Worker Down:** Stop the `rq worker` process and upload a file.
  - **Verify:** The UI stays on "Queued". Start the worker again, and the job should immediately pick up and complete.
- **STT Failure:** Temporarily change the Gnan.ai API URL or API key in `.env` to be invalid. Upload a file.
  - **Verify:** The job transitions to `FAILED`, and the UI displays a sanitized error like "The speech-to-text service is currently unavailable."
- **LLM Failure:** Temporarily break the Gemini API key in `.env`. Upload a file.
  - **Verify:** The job progresses past "Transcribing" but fails at "Summarizing", displaying a safe error message on the frontend.

---

## Interview Explanation

> "In Phase 10, I focused on application reliability. I wrote comprehensive backend test suites covering the API endpoints, database CRUD operations, and the background worker logic. By heavily mocking external services like S3 and the AI APIs, the tests run instantly and don't cost any API credits. I specifically verified that our worker correctly sanitizes exceptions so we don't leak stack traces to the database. Additionally, I documented a manual end-to-end test plan to ensure the frontend properly reflects both successful AI pipelines and unexpected API failures."
