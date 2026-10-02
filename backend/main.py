import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models, schemas, crud
import storage_service
from fastapi import BackgroundTasks
from tasks import process_audio

# Create tables (we also have alembic, but this is safe)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Audio Notes API")

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
origins = [frontend_url]
# Also allow local dev domain if frontend_url is different
if "localhost" not in frontend_url:
    origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


MAX_FILE_SIZE = 100 * 1024 * 1024 # 100 MB
ALLOWED_TYPES = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/ogg", "audio/webm", "audio/flac", "audio/x-m4a"]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/uploads", response_model=schemas.UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file (MP3, WAV, M4A, OGG, WEBM, FLAC).")
    
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 100 MB.")
    
    # Object storage for Phase 4
    file_id = str(uuid.uuid4())
    safe_filename = file.filename.replace(" ", "_")
    storage_key = f"{file_id}_{safe_filename}"
    
    # Upload to Object Storage
    success = storage_service.upload_file(file.file, storage_key, content_type=file.content_type)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload file to storage.")
        
    # Create DB record
    upload_in = schemas.UploadCreate(filename=file.filename, storage_key=storage_key)
    db_upload = crud.create_upload(db, upload_in)
    
    # Enqueue background job
    db_upload = crud.update_upload_status(db, db_upload.id, status="QUEUED", progress=0)
    
    # Push job to BackgroundTasks
    background_tasks.add_task(process_audio, str(db_upload.id))
    
    return db_upload

@app.get("/uploads/{upload_id}", response_model=schemas.UploadResponse)
def get_upload_status(upload_id: uuid.UUID, db: Session = Depends(get_db)):
    db_upload = crud.get_upload(db, upload_id)
    if not db_upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return db_upload
