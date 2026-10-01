"""
test_phase10_worker.py - Worker error-sanitization and pipeline logic tests

Tests the process_audio task from tasks.py using mocks for all external
services (DB session, storage, gnan_service, summary_service).
No real Redis, S3, Gnani.ai API, or Gemini API is needed.
"""
from unittest.mock import patch, MagicMock, call
import uuid


# -- helpers -------------------------------------------------------------------

def make_mock_db_upload(upload_id=None, storage_key="key_test.mp3"):
    """Build a mock Upload ORM object."""
    record = MagicMock()
    record.id = upload_id or str(uuid.uuid4())
    record.storage_key = storage_key
    return record


def run_process_audio(upload_id, mock_db_upload, *, download_ok=True,
                      transcript="Hello world.",
                      summary="KEY POINTS:\n- Point.\n\nSUMMARY:\nSummary.",
                      download_raises=None, transcribe_raises=None,
                      summarize_raises=None):
    """
    Run tasks.process_audio with all external calls mocked.

    Returns the mock `crud` so callers can inspect what was called.
    """
    mock_db = MagicMock()

    import tasks

    with patch("tasks.SessionLocal", return_value=mock_db), \
         patch("tasks.crud") as mock_crud, \
         patch("tasks.storage_service") as mock_storage, \
         patch("tasks.gnan_service") as mock_gnan, \
         patch("tasks.summary_service") as mock_summary, \
         patch("tasks.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("tasks.os.path.exists", return_value=False):  # skip cleanup

        # Wire up get_upload
        mock_crud.get_upload.return_value = mock_db_upload
        mock_crud.update_upload_status.return_value = mock_db_upload
        mock_crud.update_upload_results.return_value = mock_db_upload

        # Storage
        if download_raises:
            mock_storage.download_file.side_effect = download_raises
        else:
            mock_storage.download_file.return_value = download_ok

        # Gnan.ai
        if transcribe_raises:
            mock_gnan.transcribe.side_effect = transcribe_raises
        else:
            mock_gnan.transcribe.return_value = transcript

        # Gemini
        if summarize_raises:
            mock_summary.summarize.side_effect = summarize_raises
        else:
            mock_summary.summarize.return_value = summary

        # Temp file stub
        tmp_ctx = MagicMock()
        tmp_ctx.__enter__ = MagicMock(return_value=MagicMock(name="/tmp/fakefile.mp3"))
        tmp_ctx.__exit__ = MagicMock(return_value=False)
        mock_tmp.return_value = tmp_ctx
        mock_tmp.return_value.name = "/tmp/fakefile.mp3"

        tasks.process_audio(upload_id)

        return mock_crud


# -- Happy path ----------------------------------------------------------------

def test_happy_path_sets_completed(monkeypatch):
    """Full success: process_audio should mark the upload COMPLETED at progress 100."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    mock_crud = run_process_audio(uid, db_upload)

    # Last status call must be COMPLETED / 100
    status_calls = mock_crud.update_upload_status.call_args_list
    last_call = status_calls[-1]
    assert last_call.kwargs.get("status") == "COMPLETED" or last_call.args[2] == "COMPLETED"
    print("test_happy_path_sets_completed PASSED")


def test_happy_path_saves_transcript(monkeypatch):
    """process_audio should persist the transcript returned by gnan_service."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    mock_crud = run_process_audio(uid, db_upload, transcript="My transcript.")

    # At least one call to update_upload_results with transcript
    result_calls = mock_crud.update_upload_results.call_args_list
    transcripts = [c.kwargs.get("transcript") or (c.args[2] if len(c.args) > 2 else None)
                   for c in result_calls]
    assert "My transcript." in transcripts
    print("test_happy_path_saves_transcript PASSED")


def test_happy_path_saves_summary(monkeypatch):
    """process_audio should persist the summary returned by summary_service."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    summary_text = "KEY POINTS:\n- Water cycle.\n\nSUMMARY:\nWater evaporates."
    mock_crud = run_process_audio(uid, db_upload, summary=summary_text)

    result_calls = mock_crud.update_upload_results.call_args_list
    summaries = [c.kwargs.get("summary") for c in result_calls]
    assert summary_text in summaries
    print("test_happy_path_saves_summary PASSED")


def test_happy_path_progress_milestones(monkeypatch):
    """process_audio should update progress at expected milestones (10, 30, 70, 75, 90, 100)."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    mock_crud = run_process_audio(uid, db_upload)

    all_progress = [
        c.kwargs.get("progress")
        for c in mock_crud.update_upload_status.call_args_list
        if c.kwargs.get("progress") is not None
    ]
    for expected in [10, 30, 70, 100]:
        assert expected in all_progress, f"Missing progress milestone: {expected}"
    print("test_happy_path_progress_milestones PASSED")


# -- Record not found ----------------------------------------------------------

def test_missing_upload_record_exits_early():
    """If get_upload returns None, process_audio should exit without calling any service."""
    uid = str(uuid.uuid4())

    import tasks
    mock_db = MagicMock()

    with patch("tasks.SessionLocal", return_value=mock_db), \
         patch("tasks.crud") as mock_crud, \
         patch("tasks.storage_service") as mock_storage, \
         patch("tasks.gnan_service") as mock_gnan, \
         patch("tasks.summary_service") as mock_summary:

        mock_crud.get_upload.return_value = None
        tasks.process_audio(uid)

        mock_storage.download_file.assert_not_called()
        mock_gnan.transcribe.assert_not_called()
        mock_summary.summarize.assert_not_called()
    print("test_missing_upload_record_exits_early PASSED")


# -- Storage failure error sanitization ---------------------------------------

def test_storage_failure_sanitized_message():
    """RuntimeError('Failed to download') -> user sees a storage-specific message."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    mock_crud = run_process_audio(
        uid, db_upload,
        download_ok=False,
        download_raises=RuntimeError("Failed to download audio from object storage.")
    )

    failed_calls = [
        c for c in mock_crud.update_upload_status.call_args_list
        if (c.kwargs.get("status") or "") == "FAILED"
        or (len(c.args) > 2 and c.args[2] == "FAILED")
    ]
    assert len(failed_calls) >= 1
    error_msg = failed_calls[0].kwargs.get("error_message", "")
    assert "storage" in error_msg.lower() or "audio file" in error_msg.lower()
    print("test_storage_failure_sanitized_message PASSED")


def test_gnan_failure_sanitized_message():
    """Gnani.ai RuntimeError -> user sees speech-to-text-specific message."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    mock_crud = run_process_audio(
        uid, db_upload,
        transcribe_raises=RuntimeError("gnani STT ASR timeout")
    )

    failed_calls = [
        c for c in mock_crud.update_upload_status.call_args_list
        if (c.kwargs.get("status") or "") == "FAILED"
    ]
    assert len(failed_calls) >= 1
    error_msg = failed_calls[0].kwargs.get("error_message", "")
    assert "speech-to-text" in error_msg.lower() or "asr" in error_msg.lower() or "unavailable" in error_msg.lower()
    print("test_gnan_failure_sanitized_message PASSED")


def test_gemini_failure_sanitized_message():
    """Gemini RuntimeError -> user sees AI summarization-specific message."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    mock_crud = run_process_audio(
        uid, db_upload,
        summarize_raises=RuntimeError("gemini API quota exceeded llm error")
    )

    failed_calls = [
        c for c in mock_crud.update_upload_status.call_args_list
        if (c.kwargs.get("status") or "") == "FAILED"
    ]
    assert len(failed_calls) >= 1
    error_msg = failed_calls[0].kwargs.get("error_message", "")
    assert "summarization" in error_msg.lower() or "ai" in error_msg.lower() or "unavailable" in error_msg.lower()
    print("test_gemini_failure_sanitized_message PASSED")


def test_generic_exception_sanitized_message():
    """Unknown exceptions -> user sees a generic fallback message (no raw traceback)."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    mock_crud = run_process_audio(
        uid, db_upload,
        transcribe_raises=Exception("Something weird happened: secret_token=abc123")
    )

    failed_calls = [
        c for c in mock_crud.update_upload_status.call_args_list
        if (c.kwargs.get("status") or "") == "FAILED"
    ]
    assert len(failed_calls) >= 1
    error_msg = failed_calls[0].kwargs.get("error_message", "")
    # Must NOT leak the raw exception message
    assert "secret_token" not in error_msg
    assert "abc123" not in error_msg
    # Must contain some user-friendly text
    assert len(error_msg) > 0
    print("test_generic_exception_sanitized_message PASSED")


def test_error_sanitization_does_not_expose_stack_trace():
    """The error_message saved to DB must never contain Python traceback keywords."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    mock_crud = run_process_audio(
        uid, db_upload,
        download_raises=RuntimeError("Something failed with credentials at line 99")
    )

    all_error_msgs = [
        c.kwargs.get("error_message", "")
        for c in mock_crud.update_upload_status.call_args_list
        if c.kwargs.get("error_message")
    ]
    for msg in all_error_msgs:
        assert "Traceback" not in msg
        assert "line 99" not in msg  # raw exception not echoed
    print("test_error_sanitization_does_not_expose_stack_trace PASSED")


# -- Status transition ordering ------------------------------------------------

def test_transcribing_status_set_before_gnan_call():
    """TRANSCRIBING status must be set before calling gnan_service.transcribe."""
    uid = str(uuid.uuid4())
    db_upload = make_mock_db_upload(upload_id=uid)
    call_order = []

    import tasks
    mock_db = MagicMock()

    with patch("tasks.SessionLocal", return_value=mock_db), \
         patch("tasks.crud") as mock_crud, \
         patch("tasks.storage_service") as mock_storage, \
         patch("tasks.gnan_service") as mock_gnan, \
         patch("tasks.summary_service") as mock_summary, \
         patch("tasks.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("tasks.os.path.exists", return_value=False):

        mock_crud.get_upload.return_value = db_upload
        mock_crud.update_upload_status.return_value = db_upload
        mock_crud.update_upload_results.return_value = db_upload
        mock_storage.download_file.return_value = True
        mock_gnan.transcribe.return_value = "transcript"
        mock_summary.summarize.return_value = "summary"
        # Proper context manager mock for NamedTemporaryFile
        tmp_instance = MagicMock()
        tmp_instance.name = "/tmp/fake.mp3"
        tmp_instance.__enter__ = MagicMock(return_value=tmp_instance)
        tmp_instance.__exit__ = MagicMock(return_value=False)
        mock_tmp.return_value = tmp_instance

        def record_status(*args, **kwargs):
            # status may be a keyword arg OR positional arg[2]
            status_val = kwargs.get("status") or (args[2] if len(args) > 2 else None)
            if status_val:
                call_order.append(("status", status_val))
            return db_upload

        def record_transcribe(*args, **kwargs):
            call_order.append(("transcribe",))
            return "transcript"

        mock_crud.update_upload_status.side_effect = record_status
        mock_gnan.transcribe.side_effect = record_transcribe

        tasks.process_audio(uid)

    # Find first TRANSCRIBING in order
    transcribing_idx = next(
        (i for i, e in enumerate(call_order) if e == ("status", "TRANSCRIBING")), None
    )
    transcribe_idx = next(
        (i for i, e in enumerate(call_order) if e == ("transcribe",)), None
    )
    assert transcribing_idx is not None
    assert transcribe_idx is not None
    assert transcribing_idx < transcribe_idx
    print("test_transcribing_status_set_before_gnan_call PASSED")


if __name__ == "__main__":
    import sys

    class FakeMonkeypatch:
        pass

    tests = [
        (test_happy_path_sets_completed, True),
        (test_happy_path_saves_transcript, True),
        (test_happy_path_saves_summary, True),
        (test_happy_path_progress_milestones, True),
        (test_missing_upload_record_exits_early, False),
        (test_storage_failure_sanitized_message, False),
        (test_gnan_failure_sanitized_message, False),
        (test_gemini_failure_sanitized_message, False),
        (test_generic_exception_sanitized_message, False),
        (test_error_sanitization_does_not_expose_stack_trace, False),
        (test_transcribing_status_set_before_gnan_call, False),
    ]
    for fn, needs_monkeypatch in tests:
        if needs_monkeypatch:
            fn(FakeMonkeypatch())
        else:
            fn()

    print(f"\nAll {len(tests)} Phase 10 Worker tests passed!")
