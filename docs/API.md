# API Reference

## Goal

Document every API endpoint in the Audio Notes Platform.

## Base URL

Local development:
```
http://localhost:8000
```

Production:
```
https://your-backend.onrender.com   (set in Phase 12)
```

---

## Endpoints

---

### GET /health

**Purpose:** Check if the backend is running.

**Request:** None

**Response:**
```json
{
  "status": "ok"
}
```

**Status codes:**
- `200` — backend is healthy

---

### POST /uploads

**Purpose:** Upload an audio file. Creates a DB record and enqueues a background processing job.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | ✅ | Audio file (MP3, WAV, M4A, OGG, WEBM, FLAC) |

**Validation:**
- File must be an audio MIME type
- Maximum 100 MB

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "QUEUED",
  "filename": "lecture.mp3",
  "created_at": "2025-01-01T10:00:00Z"
}
```

**Status codes:**
- `201` — upload accepted, job enqueued
- `400` — invalid file type or missing file
- `413` — file too large
- `500` — server error (storage or database failure)

---

### GET /uploads/{id}

**Purpose:** Get the current status of an upload. Frontend polls this endpoint.

**Request:** Path parameter `id` (UUID)

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "lecture.mp3",
  "status": "COMPLETED",
  "progress": 100,
  "transcript": "Hello everyone, today we will discuss...",
  "summary": "## Summary\n\n**Main topic:** Machine learning basics\n\n**Key points:**\n- ...",
  "error_message": null,
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-01T10:02:30Z"
}
```

**Possible status values:**
| Status | progress | transcript | summary | error_message |
|--------|----------|-----------|---------|---------------|
| `UPLOADING` | 10 | null | null | null |
| `QUEUED` | 20 | null | null | null |
| `TRANSCRIBING` | 30–70 | null | null | null |
| `SUMMARIZING` | 75–90 | populated | null | null |
| `COMPLETED` | 100 | populated | populated | null |
| `FAILED` | unchanged | null or partial | null | populated |

**Status codes:**
- `200` — record found
- `404` — upload not found

---

## Error Response Format

All error responses follow:

```json
{
  "detail": "Human-readable error message"
}
```

Example:
```json
{
  "detail": "Invalid file type. Please upload an audio file (MP3, WAV, M4A, OGG, WEBM, FLAC)."
}
```

---

## CORS

The backend allows requests from the frontend origin.

In development:
```
http://localhost:3000
```

In production: the Vercel deployment URL.

---

## Authentication

This application does not implement user authentication (out of scope for the assignment).

In a production system, you would add:
- JWT tokens
- Or session-based auth
- And restrict `/uploads/{id}` to the owner of the upload
