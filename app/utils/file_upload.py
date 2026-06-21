import os
import aiofiles
from fastapi import UploadFile, HTTPException
from typing import List
from uuid import uuid4
from pathlib import Path

from app.core.config import settings

class FileUploadService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIRECTORY)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file: UploadFile, subfolder: str = "") -> dict:
        """Upload a single file"""
        
        # Validate file type
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file.content_type} not allowed"
            )

        # Check file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
            )

        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid4()}{file_extension}"
        
        # Create subfolder path
        folder_path = self.upload_dir / subfolder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        file_path = folder_path / unique_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "url": f"/static/{subfolder}/{unique_filename}" if subfolder else f"/static/{unique_filename}",
            "size": len(content),
            "content_type": file.content_type
        }

    async def upload_multiple_files(self, files: List[UploadFile], subfolder: str = "") -> List[dict]:
        """Upload multiple files"""
        uploaded_files = []
        
        for file in files:
            try:
                result = await self.upload_file(file, subfolder)
                uploaded_files.append(result)
            except Exception as e:
                # Log error and continue with other files
                print(f"Error uploading file {file.filename}: {str(e)}")
                continue
        
        return uploaded_files

    def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            full_path = self.upload_dir / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception:
            return False

# Utility functions
def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    try:
        uuid4(uuid_string)
        return True
    except ValueError:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()

def get_file_size_mb(size_bytes: int) -> float:
    """Convert bytes to MB"""
    return size_bytes / (1024 * 1024)