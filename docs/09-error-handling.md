# Phase 9 — Error Handling

> **Status:** ✅ Implemented

## Goal

Ensure the system gracefully handles all unexpected failures without leaking sensitive internal information (like stack traces or API keys) to the frontend, while providing useful, user-friendly error messages.

---

## What was implemented

### 1. FastAPI Global Exception Handler (`main.py`)
Previously, unhandled exceptions in the web endpoints could cause FastAPI to leak stack traces if not configured properly or result in unhelpful 500 HTML responses. 
- Added an `@app.exception_handler(Exception)` that catches any unhandled `Exception` in the FastAPI app.
- Logs the full traceback server-side using Python's standard `logging` library.
- Returns a standardized JSON response: `{"detail": "An internal server error occurred. Please try again later."}` with a `500` status code.

### 2. Worker Error Sanitization (`tasks.py`)
The background worker used to save the raw exception string `str(e)` directly into the database's `error_message` column, which was then displayed verbatim on the frontend. This could accidentally expose an API key embedded in an HTTP library error or reveal database internal schemas.
- The `except Exception as e:` block now logs the full traceback securely to the terminal/worker logs via `traceback.format_exc()`.
- Implemented a sanitization block that inspects the exception and translates it into a safe, generic `user_error`:
  - Storage errors -> *"Processing failed: Unable to read the audio file from storage."*
  - Gnan.ai errors -> *"Processing failed: The speech-to-text service is currently unavailable."*
  - Gemini LLM errors -> *"Processing failed: The AI summarization service is currently unavailable."*
  - Generic errors -> *"An unexpected error occurred during processing."*
- Only the sanitized `user_error` is saved to the database.

### 3. Frontend Error Rendering (`StatusPanel.tsx` & `UploadForm.tsx`)
(Completed in Phase 8, but relevant here)
- The frontend gracefully handles the sanitized error messages. 
- Displays them in a styled red alert box (`.status-error`).
- Halts polling on the `FAILED` state to prevent unnecessary backend load when a job is dead.

---

## Why this matters

- **Security:** Hides internal architecture and sensitive tokens from potential attackers analyzing the frontend network requests.
- **User Experience (UX):** A user seeing "Connection refused to 127.0.0.1:6379" means nothing to them. Seeing "The AI summarization service is currently unavailable" gives them actionable context (it's a backend service issue, try again later).
- **Debugging:** Developers still get the full stack trace in the backend/worker console logs where it belongs.

---

## Interview Explanation

> "In Phase 9, I hardened the application's error handling. On the API side, I added a global exception handler in FastAPI that catches any unhandled errors, logs the stack trace server-side, and returns a generic 500 JSON response so we never leak internal paths or secrets. On the background worker side, I noticed we were saving raw Python exceptions directly to the database. I rewrote the catch block to log the real traceback securely, but map the error to a sanitized, user-friendly string—like 'Speech-to-text service unavailable'—before saving it to the database. This ensures the frontend UI is both secure and helpful to the user."

