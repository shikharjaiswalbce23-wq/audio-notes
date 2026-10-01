import os
import tempfile
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import storage_service
import gnan_service
import summary_service


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def process_audio(upload_id: str):
    """
    RQ background task — runs in the worker process.

    Pipeline:
      1. Download audio from S3 into a temp file
      2. Call Gnan.ai ASR → transcript
      3. Store transcript in DB
      4. Summarize (Phase 7 — placeholder for now)
      5. Mark as COMPLETED
    """
    db: Session = next(get_db())

    try:
        # ── 1. Fetch upload record ───────────────────────────────────────────
        db_upload = crud.get_upload(db, upload_id)
        if not db_upload:
            print(f"[worker] Upload {upload_id} not found — aborting.")
            return

        print(f"[worker] Starting process_audio for {upload_id}")
        crud.update_upload_status(db, upload_id, status="TRANSCRIBING", progress=10)

        # ── 2. Download audio from S3 into a temp file ───────────────────────
        storage_key = db_upload.storage_key
        suffix = os.path.splitext(storage_key)[-1] or ".audio"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name

        try:
            print(f"[worker] Downloading {storage_key} → {tmp_path}")
            ok = storage_service.download_file(storage_key, tmp_path)
            if not ok:
                raise RuntimeError("Failed to download audio from object storage.")

            crud.update_upload_status(db, upload_id, progress=30)

            # ── 3. Transcribe with Gnan.ai ────────────────────────────────────
            print(f"[worker] Sending {tmp_path} to Gnan.ai ASR…")
            transcript = gnan_service.transcribe(tmp_path)
            print(f"[worker] Transcript received ({len(transcript)} chars)")

        finally:
            # Always clean up the temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        crud.update_upload_status(db, upload_id, progress=70)
        crud.update_upload_results(db, upload_id, transcript=transcript)

        # ── 4. Summarize with Gemini LLM ─────────────────────────────────────
        crud.update_upload_status(db, upload_id, status="SUMMARIZING", progress=75)
        print(f"[worker] Sending transcript to Gemini for summarization…")
        summary = summary_service.summarize(transcript)
        print(f"[worker] Summary received ({len(summary)} chars)")
        crud.update_upload_results(db, upload_id, summary=summary)
        crud.update_upload_status(db, upload_id, progress=90)

        # ── 5. Mark as COMPLETED ─────────────────────────────────────────────
        crud.update_upload_status(db, upload_id, status="COMPLETED", progress=100)
        print(f"[worker] Completed {upload_id}")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[worker] Job FAILED for {upload_id}:\n{error_details}")
        
        # Sanitize error message for user
        user_error = "An unexpected error occurred during processing."
        
        if isinstance(e, ValueError):
            user_error = "Processing failed: Invalid audio file or configuration."
        elif "download" in str(e).lower():
            user_error = "Processing failed: Unable to read the audio file from storage."
        elif "gnani" in str(e).lower() or "asr" in str(e).lower():
            user_error = "Processing failed: The speech-to-text service is currently unavailable."
        elif "gemini" in str(e).lower() or "llm" in str(e).lower():
            user_error = "Processing failed: The AI summarization service is currently unavailable."

        crud.update_upload_status(
            db,
            upload_id,
            status="FAILED",
            error_message=user_error,
        )
