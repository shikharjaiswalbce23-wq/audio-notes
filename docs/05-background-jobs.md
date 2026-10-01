# Phase 5 — Background Jobs

> **Status:** ✅ Implemented in Phase 5

This document covers:
- Redis setup
- RQ worker
- Enqueueing a job from FastAPI
- Dummy process_audio() job

---

## Redis Setup

We use **Redis** as a message broker to hold background jobs in a queue.
In `backend/.env`, we added a configuration for the Redis connection:
```env
REDIS_URL=redis://localhost:6379/0
```

## RQ Worker (`worker.py`)

We use **RQ (Redis Queue)** because it's a simple, lightweight library for queueing jobs and processing them in the background with workers. 
We created `backend/worker.py`, a script that connects to Redis and listens to the `default` queue. This script runs independently from the FastAPI server.

## The Dummy Job (`tasks.py`)

We created `backend/tasks.py` which contains the `process_audio(upload_id)` function. This function simulates the long-running process of transcribing and summarizing the audio by:
1. Fetching the upload record from the DB.
2. Setting the status to `PROCESSING` and progress to `10%`.
3. Sleeping for a few seconds to simulate the work.
4. Updating progress at various steps (`50%`, `90%`).
5. Marking the job as `COMPLETED` (`100%`) with a dummy transcript and summary.

*(Note: Actual transcription and summarization will be implemented in Phases 6 and 7).*

## Enqueueing a job from FastAPI (`main.py`)

In the FastAPI server (`main.py`), we initialize the Redis connection and the RQ `Queue`.
When a user successfully uploads an audio file to the `/uploads` endpoint, we:
1. Save the file to S3 (Phase 4).
2. Create the Database record.
3. Queue the background job by calling `q.enqueue(process_audio, str(db_upload.id))`.

This allows the FastAPI endpoint to respond immediately (HTTP 201) while the heavy lifting happens in the background. The client can poll the `/uploads/{upload_id}` endpoint to track the status.

> **Note:** In Phase 6, `tasks.py` was upgraded to call the real Gnan.ai ASR API instead of sleeping. The pipeline is now: download → transcribe → summarize (placeholder) → COMPLETED.
