import io
from fastapi.testclient import TestClient
from main import app
import storage_service

# Mock the storage service so it doesn't actually hit S3
original_upload_file = storage_service.upload_file

def mock_upload_file(file_obj, storage_key, content_type=None):
    print(f"MOCK: Uploaded to S3 with key {storage_key}")
    return True

storage_service.upload_file = mock_upload_file

client = TestClient(app)

def test_upload():
    # Create a fake audio file
    fake_file = io.BytesIO(b"fake audio content")
    fake_file.name = "test_audio.mp3"

    response = client.post(
        "/uploads",
        files={"file": ("test_audio.mp3", fake_file, "audio/mpeg")}
    )

    print("Response status code:", response.status_code)
    print("Response JSON:", response.json())
    
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["filename"] == "test_audio.mp3"
    print("Test passed successfully!")

if __name__ == "__main__":
    test_upload()
    # Restore original
    storage_service.upload_file = original_upload_file
