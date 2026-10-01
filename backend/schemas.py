from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class UploadCreate(BaseModel):
    filename: str
    storage_key: str

class UploadResponse(BaseModel):
    id: UUID4
    filename: str
    status: str
    progress: int
    transcript: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
