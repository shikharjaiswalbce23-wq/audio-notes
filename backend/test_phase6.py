"""
Phase 6 tests — gnan_service unit tests (Gnani.ai Vachana STT API)

Tests mock the HTTP call so no real API key or network is required.
API reference: https://docs.gnani.ai/api/STT/speech-to-text
"""
import os
import tempfile
from unittest.mock import patch, MagicMock
import gnan_service


# ── helpers ──────────────────────────────────────────────────────────────────

def make_mock_response(status_code=200, json_body=None, text=""):
    """Build a fake requests.Response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_body or {}
    mock_resp.text = text
    return mock_resp


def make_audio_file():
    """Create a temporary fake audio file and return its path."""
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.write(b"fake audio bytes")
    f.close()
    return f.name


# ── tests ─────────────────────────────────────────────────────────────────────

def test_transcribe_success():
    """Happy path: API returns { 'success': true, 'transcript': '...' }"""
    expected = "Hello, this is a test transcript."
    tmp = make_audio_file()

    try:
        with patch.dict(os.environ, {"GNANI_API_KEY": "test-key"}):
            gnan_service.GNANI_API_KEY = "test-key"
            with patch("gnan_service.requests.post") as mock_post:
                mock_post.return_value = make_mock_response(
                    status_code=200,
                    json_body={"success": True, "transcript": expected, "request_id": "req_001"},
                )
                result = gnan_service.transcribe(tmp)

        assert result == expected
        # Verify correct header and form field were used
        call_kwargs = mock_post.call_args
        assert "X-API-Key-ID" in call_kwargs.kwargs["headers"]
        assert "audio_file" in call_kwargs.kwargs["files"]
        assert call_kwargs.kwargs["data"]["language_code"] == "en-IN"
        print(f"test_transcribe_success PASSED — transcript: '{result}'")
    finally:
        os.remove(tmp)


def test_transcribe_api_failure_flag():
    """API returns 200 but success=false — RuntimeError should be raised."""
    tmp = make_audio_file()
    try:
        gnan_service.GNANI_API_KEY = "test-key"
        with patch("gnan_service.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(
                status_code=200,
                json_body={
                    "success": False,
                    "error": {"type": "INVALID_REQUEST_ERROR", "message": "Bad audio file."},
                },
            )
            raised = False
            try:
                gnan_service.transcribe(tmp)
            except RuntimeError as e:
                raised = True
                print(f"test_transcribe_api_failure_flag PASSED — caught: {e}")
            assert raised, "Expected RuntimeError but none was raised"
    finally:
        os.remove(tmp)


def test_transcribe_http_error_raises():
    """API returns 4xx/5xx status code → RuntimeError should be raised."""
    tmp = make_audio_file()
    try:
        gnan_service.GNANI_API_KEY = "test-key"
        with patch("gnan_service.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(
                status_code=429,
                text='{"success": false, "error": {"type": "RATE_LIMIT_ERROR", "message": "Rate limit exceeded."}}',
            )
            raised = False
            try:
                gnan_service.transcribe(tmp)
            except RuntimeError as e:
                raised = True
                print(f"test_transcribe_http_error_raises PASSED — caught: {e}")
            assert raised, "Expected RuntimeError but none was raised"
    finally:
        os.remove(tmp)


def test_transcribe_missing_api_key_raises():
    """Missing GNANI_API_KEY → ValueError should be raised."""
    tmp = make_audio_file()
    gnan_service.GNANI_API_KEY = None  # patch module-level var directly
    try:
        raised = False
        try:
            gnan_service.transcribe(tmp)
        except ValueError as e:
            raised = True
            print(f"test_transcribe_missing_api_key_raises PASSED — caught: {e}")
        assert raised, "Expected ValueError but none was raised"
    finally:
        os.remove(tmp)
        gnan_service.GNANI_API_KEY = os.getenv("GNANI_API_KEY")


def test_transcribe_custom_language():
    """language_code arg is forwarded correctly in the request."""
    tmp = make_audio_file()
    try:
        gnan_service.GNANI_API_KEY = "test-key"
        with patch("gnan_service.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(
                status_code=200,
                json_body={"success": True, "transcript": "नमस्ते"},
            )
            result = gnan_service.transcribe(tmp, language_code="hi-IN")
            assert result == "नमस्ते"
            sent_data = mock_post.call_args.kwargs["data"]
            assert sent_data["language_code"] == "hi-IN"
            print(f"test_transcribe_custom_language PASSED — lang forwarded as hi-IN")
    finally:
        os.remove(tmp)


if __name__ == "__main__":
    test_transcribe_success()
    test_transcribe_api_failure_flag()
    test_transcribe_http_error_raises()
    test_transcribe_missing_api_key_raises()
    test_transcribe_custom_language()
    print("\nAll Phase 6 tests passed!")
