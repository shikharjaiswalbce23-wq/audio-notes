# Phase 6 — Gnani.ai Transcription

> **Status:** ✅ Implemented in Phase 6

This document covers:
- Gnani.ai (Vachana) STT REST API integration
- `gnan_service.py` — request/response format
- Error handling
- Environment variables: `GNANI_API_KEY`, `GNANI_API_URL`, `GNANI_LANGUAGE_CODE`

---

## What is Gnani.ai?

Gnani.ai (product: **Vachana**) is an ASR (Automatic Speech Recognition) service specialised for 10 Indian languages. The REST endpoint transcribes a pre-recorded audio clip synchronously in a single HTTP request.

> **Note:** The REST endpoint is best for clips **≤ 60 seconds** (ideal ≤ 30 s). For longer audio, the [Batch STT](https://docs.gnani.ai/api/STTBatch/Introduction) API should be used in a future phase.

---

## Endpoint

```
POST https://api.vachana.ai/stt/v3
Content-Type: multipart/form-data
```

---

## Authentication

The API uses a custom header (not Bearer token):

| Header | Description |
|--------|-------------|
| `X-API-Key-ID` | Your Gnani Prisma v2.5 API key |

---

## Environment Variable Configuration

Add the following to `backend/.env`:

```env
# Gnani.ai (Vachana) STT Configuration
# Docs: https://docs.gnani.ai/api/STT/speech-to-text
GNANI_API_KEY=your_gnani_api_key
GNANI_API_URL=https://api.vachana.ai/stt/v3
GNANI_LANGUAGE_CODE=en-IN
```

- `GNANI_API_KEY` — Your secret API key. **Never expose this to the frontend.**
- `GNANI_API_URL` — Override for testing (e.g. point to a mock server).
- `GNANI_LANGUAGE_CODE` — Default BCP-47 language code. Supported values:

| Language | Code |
|----------|------|
| English (India) | `en-IN` |
| Hindi | `hi-IN` |
| Bengali | `bn-IN` |
| Gujarati | `gu-IN` |
| Kannada | `kn-IN` |
| Malayalam | `ml-IN` |
| Marathi | `mr-IN` |
| Punjabi | `pa-IN` |
| Tamil | `ta-IN` |
| Telugu | `te-IN` |

---

## gnan_service.py

```python
gnan_service.transcribe(audio_path, language_code=None, format="transcribe") → str
```

**What it does:**
1. Opens the local audio file from `audio_path`
2. POSTs it as `multipart/form-data` to `GNANI_API_URL`
3. Sets the `X-API-Key-ID` header
4. Sends `language_code` and `format` as form fields
5. Uses a 5-minute timeout (for large files)
6. Checks `response.json()["success"]` — raises `RuntimeError` if `false`
7. Returns `response.json()["transcript"]` as a string

### Request Format

```http
POST https://api.vachana.ai/stt/v3
X-API-Key-ID: <your-api-key>
Content-Type: multipart/form-data

audio_file=<binary audio bytes>
language_code=en-IN
format=transcribe
```

### Response Format (200 OK)

```json
{
  "success": true,
  "request_id": "req_abc123",
  "timestamp": "20251226_143052.123",
  "transcript": "Hello, this is the transcribed text."
}
```

### `format` Parameter

| Value | Behaviour |
|-------|-----------|
| `verbatim` | Raw spoken-form output (what the model heard) |
| `transcribe` | Enables Inverse Text Normalization (ITN): numbers, currency, dates, phone numbers in standard written form |

We default to `"transcribe"` for cleaner, more readable transcripts.

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| `GNANI_API_KEY` not set | Raises `ValueError` immediately |
| HTTP 4xx / 5xx response | Raises `RuntimeError` with status code + body |
| `success: false` in JSON body | Raises `RuntimeError` with the error message |
| No `transcript` field | Raises `RuntimeError` with raw body |
| Network timeout | `requests.Timeout` propagates; worker catches it → `FAILED` status |

All exceptions bubble up to `tasks.process_audio()`, which catches them and sets `status = "FAILED"` with a descriptive `error_message`.

---

## Updated tasks.py Pipeline

```
status = TRANSCRIBING, progress = 10
        ↓
Download audio from S3 → temp file
        ↓
progress = 30
        ↓
gnan_service.transcribe(tmp_path) → transcript string
        ↓
Delete temp file (always, even on error)
        ↓
progress = 70 | store transcript in DB
        ↓
status = SUMMARIZING, progress = 75   ← (Phase 7 placeholder)
        ↓
status = COMPLETED, progress = 100
```
