from pydantic import BaseModel
from typing import Optional, Dict, Any

class ImageGenerationResponse(BaseModel):
    success: bool
    image_url: str
    original_prompt: str
    enhanced_prompt: str
    generation_time: float

class CaptionGenerationResponse(BaseModel):
    success: bool
    caption: str
    character_count: int
    hashtag_count: int
    platform: str

class ImageEditResponse(BaseModel):
    success: bool
    edited_image_url: str
    edit_description: str

class PreviewResponse(BaseModel):
    success: bool
    preview_data: Dict[str, Any]
    warnings: Optional[list] = []

class PostPublishResponse(BaseModel):
    success: bool
    post_id: Optional[str] = None
    platform: str
    post_url: Optional[str] = None
    error: Optional[str] = None