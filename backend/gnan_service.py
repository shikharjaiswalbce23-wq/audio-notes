import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

GNANI_API_KEY = os.getenv("GNANI_API_KEY")
GNANI_API_URL = os.getenv("GNANI_API_URL", "https://api.vachana.ai/stt/v3")
GNANI_LANGUAGE_CODE = os.getenv("GNANI_LANGUAGE_CODE", "en-IN")


def transcribe(audio_path: str, language_code: str = None, format: str = "transcribe") -> str:
    """
    Send an audio file to the Gnani.ai (Vachana) STT API and return the transcript text.
    Automatically uses the synchronous REST API for short files (< 1.5MB) and the Batch 
    API for long audio files (> 1.5MB).

    Args:
        audio_path:     Absolute path to the local audio file to transcribe.
        language_code:  BCP-47 code, e.g. "en-IN", "hi-IN". Falls back to
                        the GNANI_LANGUAGE_CODE env var (default "en-IN").
        format:         "verbatim" (raw spoken form) or "transcribe" (enables
                        Inverse Text Normalization — ITN). Defaults to
                        "transcribe" for cleaner output.

    Returns:
        The transcript as a plain string.
    """
    if not GNANI_API_KEY:
        raise ValueError("GNANI_API_KEY environment variable is not set.")

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    # Also use batch if size > 1.0 MB as a generic heuristic to save the roundtrip
    if file_size_mb > 1.0:
        print(f"[gnan_service] File size is {file_size_mb:.2f}MB, using Batch API for long audio.")
        return _transcribe_batch(audio_path, language_code, format)
    else:
        print(f"[gnan_service] File size is {file_size_mb:.2f}MB, trying Sync API for short audio.")
        try:
            return _transcribe_sync(audio_path, language_code, format)
        except RuntimeError as e:
            if "MAX_AUDIO_DURATION_EXCEEDED" in str(e):
                print(f"[gnan_service] Sync API failed due to duration > 30s. Falling back to Batch API.")
                return _transcribe_batch(audio_path, language_code, format)
            raise e


def _transcribe_sync(audio_path: str, language_code: str = None, format: str = "transcribe") -> str:
    lang = language_code or GNANI_LANGUAGE_CODE

    with open(audio_path, "rb") as f:
        filename = os.path.basename(audio_path)
        files = {"audio_file": (filename, f)}
        headers = {"X-API-Key-ID": GNANI_API_KEY}
        data = {
            "language_code": lang,
            "format": format,
        }

        response = requests.post(
            GNANI_API_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=300,  # 5-minute timeout for long audio
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Gnani.ai STT API error {response.status_code}: {response.text}"
        )

    body = response.json()

    # Expected response: { "success": true, "transcript": "...", ... }
    if not body.get("success"):
        error_info = body.get("error", {})
        raise RuntimeError(
            f"Gnani.ai STT API returned failure: {error_info.get('message', body)}"
        )

    transcript = body.get("transcript")
    if transcript is None:
        raise RuntimeError(
            f"Gnani.ai STT API returned unexpected response format: {body}"
        )

    return transcript


def _transcribe_batch(audio_path: str, language_code: str = None, format: str = "transcribe") -> str:
    lang = language_code or GNANI_LANGUAGE_CODE
    
    # Base URL for batch (e.g., https://api.vachana.ai/stt/v3/batch/jobs)
    base_batch_url = GNANI_API_URL.rstrip("/") + "/batch/jobs"
    headers = {"X-API-Key-ID": GNANI_API_KEY}

    # 1. Create Job
    with open(audio_path, "rb") as f:
        filename = os.path.basename(audio_path)
        files = {"audio_file": (filename, f)}
        data = {
            "language_code": lang,
            "format": format,
        }
        create_resp = requests.post(base_batch_url, headers=headers, files=files, data=data, timeout=60)
        
    if create_resp.status_code not in (200, 201):
        raise RuntimeError(f"Gnani.ai Batch API create error {create_resp.status_code}: {create_resp.text}")
        
    create_body = create_resp.json()
    job_id = create_body.get("job_id")
    if not job_id:
        raise RuntimeError(f"No job_id returned from batch create: {create_body}")
        
    print(f"[gnan_service] Batch job created: {job_id}. Starting job...")
        
    # 2. Start Job
    start_url = f"{base_batch_url}/{job_id}/start"
    start_resp = requests.post(start_url, headers=headers, timeout=30)
    if start_resp.status_code not in (200, 201):
        raise RuntimeError(f"Gnani.ai Batch API start error {start_resp.status_code}: {start_resp.text}")
        
    print(f"[gnan_service] Batch job {job_id} started. Polling for completion...")

    # 3. Poll Status
    status_url = f"{base_batch_url}/{job_id}"
    while True:
        status_resp = requests.get(status_url, headers=headers, timeout=30)
        if status_resp.status_code != 200:
            raise RuntimeError(f"Gnani.ai Batch API status error {status_resp.status_code}: {status_resp.text}")
            
        status_body = status_resp.json()
        status = status_body.get("status", "").upper()
        
        if status == "COMPLETED":
            print(f"[gnan_service] Batch job {job_id} completed.")
            break
        elif status in ("FAILED", "ERROR"):
            error_info = status_body.get("error", {})
            raise RuntimeError(f"Gnani.ai Batch API job failed: {error_info}")
            
        time.sleep(5) # Poll every 5 seconds
        
    # 4. Retrieve Files & Download Transcript
    files_url = f"{base_batch_url}/{job_id}/files"
    files_resp = requests.get(files_url, headers=headers, timeout=30)
    if files_resp.status_code != 200:
        raise RuntimeError(f"Gnani.ai Batch API files error {files_resp.status_code}: {files_resp.text}")
        
    files_body = files_resp.json()
    
    # The API returns a list of files or an object containing a list of files.
    transcript_url = None
    if isinstance(files_body, list) and len(files_body) > 0:
        transcript_url = files_body[0].get("transcript_url")
    elif isinstance(files_body, dict):
        if "transcript_url" in files_body:
            transcript_url = files_body.get("transcript_url")
        elif "files" in files_body and isinstance(files_body["files"], list) and len(files_body["files"]) > 0:
            transcript_url = files_body["files"][0].get("transcript_url")
            
    if not transcript_url:
        raise RuntimeError(f"No transcript_url in batch files response: {files_body}")
        
    print(f"[gnan_service] Downloading transcript from {transcript_url}...")
    dl_resp = requests.get(transcript_url, timeout=60)
    if dl_resp.status_code != 200:
        raise RuntimeError(f"Failed to download transcript from {transcript_url}: {dl_resp.status_code}")
        
    dl_body = dl_resp.json()
    transcript = dl_body.get("full_transcript") or dl_body.get("transcript")
    if transcript is None:
        raise RuntimeError(f"Gnani.ai Batch API returned unexpected transcript format: {dl_body}")
        
    return transcript
