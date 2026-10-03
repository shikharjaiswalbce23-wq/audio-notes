import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GNANI_API_KEY = os.getenv("GNANI_API_KEY")
GNANI_API_URL = os.getenv(
    "GNANI_API_URL",
    "https://api.vachana.ai/stt/v3"
)


def transcribe_batch(
    audio_path: str,
    language_code: str = "en-IN"
) -> str:

    if not GNANI_API_KEY:
        raise ValueError("GNANI_API_KEY is not set.")

    base_url = GNANI_API_URL.rstrip("/")
    batch_url = f"{base_url}/batch/jobs"

    headers = {
        "X-API-Key-ID": GNANI_API_KEY
    }

    # --------------------------------
    # 1. CREATE JOB
    # --------------------------------

    config = {
        "model": "gnani-prisma-v2.5",
        "language_code": language_code,
        "mode": "transcribe",
        "with_diarization": False,
        "is_multi_channel": False
    }

    with open(audio_path, "rb") as audio:

        files = {
            "files": (
                os.path.basename(audio_path),
                audio
            )
        }

        data = {
            "config": json.dumps(config)
        }

        response = requests.post(
            batch_url,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Create job failed "
            f"{response.status_code}: {response.text}"
        )

    body = response.json()

    job_id = body.get("job_id")

    if not job_id:
        raise RuntimeError(
            f"No job_id returned: {body}"
        )

    print(f"Created Batch job: {job_id}")

    # --------------------------------
    # 2. START JOB
    # --------------------------------

    start_url = f"{batch_url}/{job_id}/start"

    response = requests.post(
        start_url,
        headers=headers,
        timeout=30
    )

    if response.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"Start job failed "
            f"{response.status_code}: {response.text}"
        )

    print(f"Started job: {job_id}")

    # --------------------------------
    # 3. POLL STATUS
    # --------------------------------

    status_url = f"{batch_url}/{job_id}"

    while True:

        response = requests.get(
            status_url,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Status request failed "
                f"{response.status_code}: {response.text}"
            )

        status_body = response.json()

        status = status_body.get("status", "").upper()

        print(f"Job {job_id}: {status}")

        if status == "COMPLETED":
            break

        if status == "PARTIAL_FAILURE":
            raise RuntimeError(
                f"Batch job partially failed: {status_body}"
            )

        if status in (
            "FAILED",
            "START_FAILED",
            "CANCELLED"
        ):
            raise RuntimeError(
                f"Batch job failed: {status_body}"
            )

        # Gnani recommends >= 10 seconds
        time.sleep(10)

    # --------------------------------
    # 4. GET COMPLETED FILES
    # --------------------------------

    files_url = f"{batch_url}/{job_id}/files"

    response = requests.get(
        files_url,
        headers=headers,
        params={"status": "COMPLETED"},
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Get files failed "
            f"{response.status_code}: {response.text}"
        )

    files_body = response.json()

    # --------------------------------
    # 5. FIND TRANSCRIPT URL
    # --------------------------------

    transcript_url = None

    if isinstance(files_body, list):

        if files_body:
            transcript_url = files_body[0].get(
                "transcript_url"
            )

    elif isinstance(files_body, dict):

        transcript_url = files_body.get(
            "transcript_url"
        )

        if not transcript_url:

            completed_files = files_body.get("files", [])

            if completed_files:
                transcript_url = completed_files[0].get(
                    "transcript_url"
                )

    if not transcript_url:
        raise RuntimeError(
            f"No transcript_url found: {files_body}"
        )

    # --------------------------------
    # 6. DOWNLOAD TRANSCRIPT
    # --------------------------------

    response = requests.get(
        transcript_url,
        timeout=60
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Transcript download failed "
            f"{response.status_code}: {response.text}"
        )

    transcript_body = response.json()

    transcript = transcript_body.get(
        "full_transcript"
    )

    if transcript is None:
        raise RuntimeError(
            f"No full_transcript found: "
            f"{transcript_body}"
        )

    return transcript

# Alias to maintain compatibility with tasks.py and tests
transcribe = transcribe_batch