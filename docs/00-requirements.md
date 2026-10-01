# Phase 0 — Requirements

## Goal

Define exactly what this application needs to do before writing a single line of code.

## Why do we need it?

Writing requirements first prevents building the wrong thing. It also gives you a clear checklist to verify against during development and in interviews.

---

## Functional Requirements

These are things the application **must do**.

| # | Requirement |
|---|-------------|
| FR-1 | User can upload an audio file through a web UI |
| FR-2 | Uploaded audio is stored in cloud object storage (not the database) |
| FR-3 | Backend creates a database record for the upload and returns an ID |
| FR-4 | A background worker transcribes the audio using Gnan.ai ASR |
| FR-5 | After transcription, a background worker summarizes the transcript using an LLM |
| FR-6 | User can see the current processing status at any time |
| FR-7 | User can see the transcript once transcription is complete |
| FR-8 | User can see the summary once summarization is complete |
| FR-9 | Failures are clearly displayed to the user with a helpful message |
| FR-10 | The frontend never freezes — all heavy work happens in the background |

---

## Non-Functional Requirements

These are quality constraints the application **must meet**.

| # | Requirement | Why |
|---|-------------|-----|
| NFR-1 | Handle audio files of 2 minutes or longer | Real-world recordings are not short |
| NFR-2 | API response to upload request must be < 3 seconds | File goes to storage; job goes to queue; done |
| NFR-3 | No API keys are exposed to the browser | Security |
| NFR-4 | No stack traces or internal errors shown to users | Security + UX |
| NFR-5 | Background job failures must be stored and retrievable | User can see what went wrong |
| NFR-6 | Application must be deployable to a public URL | Assignment requirement |
| NFR-7 | Code must be simple and readable | Assignment requirement + interview clarity |

---

## Status Model

The `status` field on an Upload record will be one of:

| Status | Meaning | Who sets it |
|--------|---------|-------------|
| `UPLOADING` | File is currently being uploaded to storage | Backend (set before upload begins) |
| `QUEUED` | File is uploaded; job is waiting in Redis queue | Backend (set after enqueue) |
| `TRANSCRIBING` | Worker is calling Gnan.ai ASR | RQ Worker |
| `SUMMARIZING` | Transcription done; worker is calling LLM | RQ Worker |
| `COMPLETED` | Both transcript and summary are stored | RQ Worker |
| `FAILED` | Something went wrong; see `error_message` | RQ Worker or Backend |

### Why each status exists

- **UPLOADING** — The file could take several seconds to reach object storage. We need a state to represent that window.
- **QUEUED** — Upload is done but the worker hasn't started yet. Redis might be busy with other jobs.
- **TRANSCRIBING** — Gnan.ai ASR can take 10–60+ seconds for long audio. User needs feedback that something is happening.
- **SUMMARIZING** — LLM API call is in progress. Separate from transcription so the user knows which step is active.
- **COMPLETED** — Terminal state. Frontend can stop polling and display results.
- **FAILED** — Terminal state. Something went wrong. `error_message` explains what.

---

## File Validation Rules

| Rule | Reason |
|------|--------|
| Only allow audio MIME types (audio/mpeg, audio/wav, audio/mp4, audio/ogg, audio/webm, audio/flac) | Prevent users from uploading arbitrary files |
| Maximum file size: 100 MB | Prevents abuse; Gnan.ai likely has limits too |
| Filename must not contain special characters | Prevents storage key injection |

---

## API Design (High-Level)

> Full API docs: see `docs/API.md`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check if the backend is alive |
| POST | `/uploads` | Upload an audio file, returns `{ id, status }` |
| GET | `/uploads/{id}` | Get status, progress, transcript, summary for an upload |

---

## Database Design (High-Level)

> Full schema: see `docs/02-database.md`

**Table: `uploads`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `filename` | TEXT | Original filename the user uploaded |
| `storage_key` | TEXT | The key/path in object storage |
| `status` | TEXT | One of the 6 statuses above |
| `progress` | INTEGER | 0–100, represents processing progress |
| `transcript` | TEXT | Full transcript text (nullable) |
| `summary` | TEXT | AI-generated summary (nullable) |
| `error_message` | TEXT | Friendly error if status = FAILED (nullable) |
| `created_at` | TIMESTAMP | When the record was created |
| `updated_at` | TIMESTAMP | When the record was last updated |

---

## Background Job Flow

```
User uploads file
       ↓
Backend stores file in S3
       ↓
Backend creates DB record (status = QUEUED)
       ↓
Backend enqueues job: process_audio(upload_id)
       ↓
RQ Worker picks up job
       ↓
Worker sets status = TRANSCRIBING
       ↓
Worker downloads audio from S3
       ↓
Worker sends audio to Gnan.ai
       ↓
Gnan.ai returns transcript
       ↓
Worker stores transcript in DB
       ↓
Worker sets status = SUMMARIZING
       ↓
Worker sends transcript to LLM
       ↓
LLM returns summary
       ↓
Worker stores summary in DB
       ↓
Worker sets status = COMPLETED, progress = 100
```

If any step fails:
```
Worker catches exception
       ↓
Worker stores error_message in DB
       ↓
Worker sets status = FAILED
```

---

## Frontend Flow

```
User opens page
       ↓
User picks audio file (file picker)
       ↓
Frontend validates file type + size
       ↓
User clicks Upload
       ↓
Frontend sends POST /uploads (multipart form)
       ↓
Backend returns { id, status }
       ↓
Frontend starts polling GET /uploads/{id} every 3 seconds
       ↓
Frontend shows status + progress bar
       ↓
When status = COMPLETED → stop polling, show transcript + summary
When status = FAILED   → stop polling, show error message
```

---

## Object Storage Flow

```
Audio file received by FastAPI
       ↓
Generate a unique storage key:  uploads/{uuid}/{filename}
       ↓
Upload bytes to S3-compatible bucket
       ↓
Store the storage key in the DB record
       ↓
(Worker later downloads using the same key)
```

---

## Deployment Architecture

```
Next.js → Vercel (free tier)
FastAPI → Render / Railway (web service)
RQ Worker → Render / Railway (worker service, same codebase)
PostgreSQL → Render / Railway managed DB
Redis → Render / Railway Redis
Object Storage → Cloudflare R2 / AWS S3
```

All backend secrets (API keys, DB URL, S3 credentials) stay in the backend environment — **never in Vercel**.

---

## Interview Explanation

> "Before writing any code, I defined all the functional and non-functional requirements. This let me design the database schema, API endpoints, and job flow upfront. For example, I chose 6 status values — UPLOADING, QUEUED, TRANSCRIBING, SUMMARIZING, COMPLETED, FAILED — because the processing pipeline has distinct stages and the user needs to see which one is active. Having clear requirements also made it easier to spot edge cases early, like what happens if Gnan.ai fails halfway through."
