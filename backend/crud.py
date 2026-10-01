from sqlalchemy.orm import Session
import models, schemas
import uuid

def create_upload(db: Session, upload: schemas.UploadCreate):
    db_upload = models.Upload(
        filename=upload.filename,
        storage_key=upload.storage_key,
        status="UPLOADING"
    )
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    return db_upload

def get_upload(db: Session, upload_id: uuid.UUID):
    return db.query(models.Upload).filter(models.Upload.id == upload_id).first()

def update_upload_status(db: Session, upload_id: uuid.UUID, status: str, progress: int = None, error_message: str = None):
    db_upload = get_upload(db, upload_id)
    if db_upload:
        db_upload.status = status
        if progress is not None:
            db_upload.progress = progress
        if error_message is not None:
            db_upload.error_message = error_message
        db.commit()
        db.refresh(db_upload)
    return db_upload

def update_upload_results(db: Session, upload_id: uuid.UUID, transcript: str = None, summary: str = None):
    db_upload = get_upload(db, upload_id)
    if db_upload:
        if transcript:
            db_upload.transcript = transcript
        if summary:
            db_upload.summary = summary
        db.commit()
        db.refresh(db_upload)
    return db_upload
