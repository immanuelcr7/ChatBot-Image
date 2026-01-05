from fastapi import HTTPException, UploadFile
from typing import Optional
import uuid

class RequestValidationLayer:
    """Layer 2: API Gateway & Request Validation"""
    
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def validate_image(self, file: UploadFile) -> bytes:
        """
        Validate image format, size, and type.
        Returns: image bytes if valid
        Raises: HTTPException if invalid
        """
        # Check content type
        if file.content_type not in self.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(self.ALLOWED_IMAGE_TYPES)}"
            )
        
        # Read and check size
        image_data = await file.read()
        if len(image_data) > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {self.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        return image_data
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize user text input.
        Remove potentially harmful characters or scripts.
        """
        if not text:
            return ""
        
        # Basic sanitization
        text = text.strip()
        
        # Limit length
        max_length = 2000
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove null bytes
        text = text.replace("\x00", "")
        
        return text
    
    def get_or_create_session_id(self, session_id: Optional[str]) -> str:
        """
        Assign or verify session ID.
        """
        if session_id and len(session_id) > 0:
            return session_id
        return str(uuid.uuid4())
