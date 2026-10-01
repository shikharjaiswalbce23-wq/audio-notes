"""
test_phase10_crud.py - CRUD layer unit tests

Uses an in-memory SQLite database so no server, real DB file, or external
service is required.  Each test gets a fresh session via the `db` fixture.
"""
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# We import models.Base to create all tables, then use crud directly.
import models
import crud
import schemas

# -- Fixtures ------------------------------------------------------------------

@pytest.fixture(scope="function")
def db():
    """Create a throwaway in-memory SQLite DB for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    models.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        models.Base.metadata.drop_all(bind=engine)


def make_upload_create(filename="test.mp3", key=None):
    """Helper: build a valid UploadCreate schema object."""
    key = key or f"{uuid.uuid4()}_test.mp3"
    return schemas.UploadCreate(filename=filename, storage_key=key)


# -- create_upload -------------------------------------------------------------

def test_create_upload_returns_record(db):
    """create_upload should persist and return an Upload with UPLOADING status."""
    upload_in = make_upload_create()
    result = crud.create_upload(db, upload_in)

    assert result.id is not None
    assert result.filename == "test.mp3"
    assert result.status == "UPLOADING"
    assert result.progress == 0
    assert result.transcript is None
    assert result.summary is None
    assert result.error_message is None
    assert result.created_at is not None
    print("test_create_upload_returns_record PASSED")


def test_create_upload_persists_to_db(db):
    """Record inserted by create_upload should be queryable from the session."""
    upload_in = make_upload_create(filename="lecture.wav")
    created = crud.create_upload(db, upload_in)

    fetched = db.query(models.Upload).filter_by(id=created.id).first()
    assert fetched is not None
    assert fetched.filename == "lecture.wav"
    print("test_create_upload_persists_to_db PASSED")


def test_create_upload_unique_ids(db):
    """Each call to create_upload generates a distinct UUID."""
    a = crud.create_upload(db, make_upload_create())
    b = crud.create_upload(db, make_upload_create())
    assert a.id != b.id
    print("test_create_upload_unique_ids PASSED")


# -- get_upload ----------------------------------------------------------------

def test_get_upload_returns_correct_record(db):
    """get_upload should return the record matching the given UUID."""
    created = crud.create_upload(db, make_upload_create())
    fetched = crud.get_upload(db, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    print("test_get_upload_returns_correct_record PASSED")


def test_get_upload_missing_id_returns_none(db):
    """get_upload with a non-existent UUID should return None (not raise)."""
    result = crud.get_upload(db, uuid.uuid4())
    assert result is None
    print("test_get_upload_missing_id_returns_none PASSED")


def test_get_upload_does_not_cross_contaminate(db):
    """get_upload should return the correct row when multiple records exist."""
    a = crud.create_upload(db, make_upload_create(filename="a.mp3"))
    b = crud.create_upload(db, make_upload_create(filename="b.mp3"))
    assert crud.get_upload(db, a.id).filename == "a.mp3"
    assert crud.get_upload(db, b.id).filename == "b.mp3"
    print("test_get_upload_does_not_cross_contaminate PASSED")


# -- update_upload_status ------------------------------------------------------

def test_update_status_changes_status_field(db):
    """update_upload_status should update the status column."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_status(db, upload.id, status="QUEUED", progress=0)
    assert crud.get_upload(db, upload.id).status == "QUEUED"
    print("test_update_status_changes_status_field PASSED")


def test_update_status_changes_progress(db):
    """update_upload_status should update progress when supplied."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_status(db, upload.id, status="TRANSCRIBING", progress=30)
    assert crud.get_upload(db, upload.id).progress == 30
    print("test_update_status_changes_progress PASSED")


def test_update_status_skips_progress_when_none(db):
    """progress=None should leave the current progress value untouched."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_status(db, upload.id, status="QUEUED", progress=5)
    crud.update_upload_status(db, upload.id, status="TRANSCRIBING", progress=None)
    assert crud.get_upload(db, upload.id).progress == 5
    print("test_update_status_skips_progress_when_none PASSED")


def test_update_status_sets_error_message(db):
    """error_message kwarg should be persisted when provided."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_status(
        db, upload.id, status="FAILED",
        error_message="Processing failed: Unable to read the audio file from storage."
    )
    refreshed = crud.get_upload(db, upload.id)
    assert refreshed.status == "FAILED"
    assert "Unable to read" in refreshed.error_message
    print("test_update_status_sets_error_message PASSED")


def test_update_status_leaves_error_message_when_not_provided(db):
    """Calling update_upload_status without error_message should not clear it."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_status(db, upload.id, status="FAILED", error_message="original error")
    crud.update_upload_status(db, upload.id, status="FAILED", progress=None)
    assert crud.get_upload(db, upload.id).error_message == "original error"
    print("test_update_status_leaves_error_message_when_not_provided PASSED")


def test_update_status_full_pipeline_progression(db):
    """Simulate the full UPLOADING -> QUEUED -> TRANSCRIBING -> SUMMARIZING -> COMPLETED pipeline."""
    upload = crud.create_upload(db, make_upload_create())
    assert crud.get_upload(db, upload.id).status == "UPLOADING"

    for status, progress in [
        ("QUEUED", 0),
        ("TRANSCRIBING", 10),
        ("TRANSCRIBING", 30),
        ("TRANSCRIBING", 70),
        ("SUMMARIZING", 75),
        ("SUMMARIZING", 90),
        ("COMPLETED", 100),
    ]:
        crud.update_upload_status(db, upload.id, status=status, progress=progress)

    final = crud.get_upload(db, upload.id)
    assert final.status == "COMPLETED"
    assert final.progress == 100
    print("test_update_status_full_pipeline_progression PASSED")


def test_update_status_invalid_id_returns_none(db):
    """update_upload_status with a non-existent ID should return None safely."""
    result = crud.update_upload_status(db, uuid.uuid4(), status="FAILED")
    assert result is None
    print("test_update_status_invalid_id_returns_none PASSED")


# -- update_upload_results -----------------------------------------------------

def test_update_results_sets_transcript(db):
    """update_upload_results should persist the transcript field."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_results(db, upload.id, transcript="Hello world.")
    assert crud.get_upload(db, upload.id).transcript == "Hello world."
    print("test_update_results_sets_transcript PASSED")


def test_update_results_sets_summary(db):
    """update_upload_results should persist the summary field."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_results(db, upload.id, summary="KEY POINTS:\n- Something.\n\nSUMMARY:\nA summary.")
    assert "KEY POINTS" in crud.get_upload(db, upload.id).summary
    print("test_update_results_sets_summary PASSED")


def test_update_results_sets_both_fields(db):
    """update_upload_results should persist both transcript and summary."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_results(db, upload.id, transcript="The transcript.", summary="The summary.")
    refreshed = crud.get_upload(db, upload.id)
    assert refreshed.transcript == "The transcript."
    assert refreshed.summary == "The summary."
    print("test_update_results_sets_both_fields PASSED")


def test_update_results_does_not_clear_transcript_when_summary_only(db):
    """Passing only summary= should not clear a previously stored transcript."""
    upload = crud.create_upload(db, make_upload_create())
    crud.update_upload_results(db, upload.id, transcript="Original transcript.")
    crud.update_upload_results(db, upload.id, summary="A summary.")
    refreshed = crud.get_upload(db, upload.id)
    assert refreshed.summary == "A summary."
    assert refreshed.transcript == "Original transcript."
    print("test_update_results_does_not_clear_transcript_when_summary_only PASSED")


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    tests = [
        test_create_upload_returns_record,
        test_create_upload_persists_to_db,
        test_create_upload_unique_ids,
        test_get_upload_returns_correct_record,
        test_get_upload_missing_id_returns_none,
        test_get_upload_does_not_cross_contaminate,
        test_update_status_changes_status_field,
        test_update_status_changes_progress,
        test_update_status_skips_progress_when_none,
        test_update_status_sets_error_message,
        test_update_status_leaves_error_message_when_not_provided,
        test_update_status_full_pipeline_progression,
        test_update_status_invalid_id_returns_none,
        test_update_results_sets_transcript,
        test_update_results_sets_summary,
        test_update_results_sets_both_fields,
        test_update_results_does_not_clear_transcript_when_summary_only,
    ]
    for t in tests:
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        models.Base.metadata.create_all(bind=eng)
        S = sessionmaker(autocommit=False, autoflush=False, bind=eng)
        s = S()
        try:
            t(s)
        finally:
            s.close()
    print(f"\nAll {len(tests)} Phase 10 CRUD tests passed!")
