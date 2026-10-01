# Phase 7 — LLM Summarization

> **Status:** ✅ Implemented

## Goal

After transcription completes, the RQ worker sends the transcript to a Large Language Model (LLM)
and stores the resulting structured summary in the database. The frontend can then display it alongside
the transcript when the status reaches `COMPLETED`.

---

## LLM Provider Choice: Google Gemini

We chose **Google Gemini** (`gemini-1.5-flash`) because:
- Free tier is generous (1,500 requests/day)
- `google-generativeai` Python SDK is simple and well-documented
- Fast response times for summarization tasks
- Easily swappable — all LLM logic is isolated in `summary_service.py`

---

## Files Changed / Added

| File | Change |
|------|--------|
| `backend/summary_service.py` | **New** — Gemini API integration |
| `backend/tasks.py` | Updated step 4 — real summarization replaces placeholder |
| `backend/requirements.txt` | Added `google-generativeai==0.8.3` |
| `backend/.env` | Added `GEMINI_API_KEY` and `GEMINI_MODEL` |
| `backend/test_phase7.py` | **New** — 8 unit tests (all mocked, no real API call) |

---

## summary_service.py

The service exposes a single function:

```python
def summarize(transcript: str) -> str:
    ...
```

**What it does:**
1. Validates `GEMINI_API_KEY` is set — raises `ValueError` if not
2. Validates the transcript is non-empty — raises `ValueError` if blank
3. Configures the Gemini SDK with the key
4. Sends the transcript inside a structured prompt
5. Validates the response is non-empty — raises `RuntimeError` if blank
6. Returns the summary as a plain string

---

## Summarization Prompt

The prompt asks the model to produce two sections — this makes it easy for the frontend
to display them separately if needed:

```
KEY POINTS:
- [First key point]
- [Second key point]
- ...

SUMMARY:
[A 2-4 sentence paragraph capturing the main idea.]
```

**Prompt design decisions:**
- Tells the model it is an "expert note-taker" — sets the right tone
- Instructs the model NOT to add outside knowledge — prevents hallucinations
- Explicitly asks it to ignore filler words (um, uh) — handles informal speech
- Requests plain text output — no markdown escaping needed in frontend

---

## How it fits into tasks.py

```python
# Step 4 in process_audio()
crud.update_upload_status(db, upload_id, status="SUMMARIZING", progress=75)
summary = summary_service.summarize(transcript)
crud.update_upload_results(db, upload_id, summary=summary)
crud.update_upload_status(db, upload_id, progress=90)
```

If `summarize()` raises, the outer `except` in `process_audio()` catches it and sets `status = FAILED`.

---

## Environment Variables

Add to `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
```

Get a free API key at: https://aistudio.google.com/app/apikey

---

## Error Handling

| Failure | Exception raised | Worker result |
|---------|-----------------|---------------|
| `GEMINI_API_KEY` not set | `ValueError` | `status=FAILED`, error stored in DB |
| Transcript is empty | `ValueError` | `status=FAILED`, error stored in DB |
| Network/SDK error | `RuntimeError` | `status=FAILED`, error stored in DB |
| Empty response from Gemini | `RuntimeError` | `status=FAILED`, error stored in DB |

---

## Tests (test_phase7.py)

8 unit tests, all mocked — no real Gemini API key required:

| Test | What it checks |
|------|---------------|
| `test_summarize_success` | Happy path — correct return value, SDK called correctly |
| `test_summarize_missing_api_key` | `ValueError` when `GEMINI_API_KEY=None` |
| `test_summarize_empty_transcript` | `ValueError` for `""` |
| `test_summarize_whitespace_only_transcript` | `ValueError` for `"  \n  "` |
| `test_summarize_api_exception` | `RuntimeError` when SDK raises |
| `test_summarize_empty_response` | `RuntimeError` when `response.text = ""` |
| `test_summarize_prompt_contains_key_points_instruction` | Prompt has `KEY POINTS:` and `SUMMARY:` |
| `test_summarize_uses_configured_model` | Model name from env var is forwarded |

Run with:
```bash
python test_phase7.py
```

---

## Interview Explanation

> "In Phase 7 I isolated LLM summarization into its own `summary_service.py` module so it is
> completely decoupled from the worker logic. This means I can swap Gemini for OpenAI or any other
> LLM by only changing one file. The prompt asks for two structured sections — KEY POINTS and SUMMARY
> — making it easy for the frontend to display them separately. All error cases raise typed exceptions
> that the worker catches, storing a friendly `error_message` in the database so the user never sees
> a raw stack trace."
