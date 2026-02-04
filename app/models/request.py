from pydantic import BaseModel, Field, validator
from typing import Optional, Literal


# ============ ADVERTISEMENT MODE MODELS ============

class GenerateProductImageRequest(BaseModel):
    """Request to generate product image from description"""
    product_description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Detailed description of the product"
    )
    style: Literal["professional", "casual", "creative", "minimalist"] = "professional"

    @validator('product_description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Product description cannot be empty')
        return v.strip()


class GenerateCaptionRequest(BaseModel):
    """Request to generate post caption"""
    content_description: str = Field(..., min_length=10)
    image_url: Optional[str] = None
    platform: Literal["instagram", "facebook", "both"] = "instagram"
    tone: Literal["professional", "casual", "friendly", "formal"] = "professional"
    include_hashtags: bool = True
    include_emojis: bool = True


# ============ GENERAL POST MODE MODELS ============

class UploadImageRequest(BaseModel):
    """Metadata for image upload"""
    description: Optional[str] = None
    should_edit: bool = False
    edit_instructions: Optional[str] = None


class EditImageRequest(BaseModel):
    """Request to edit/enhance existing image"""
    image_url: str
    edit_instructions: str = Field(
        ...,
        min_length=5,
        description="Instructions for how to edit the image"
    )


# ============ POSTING MODELS ============

class PreviewPostRequest(BaseModel):
    """Preview post before publishing"""
    image_url: str
    caption: str
    platform: Literal["instagram", "facebook", "both"]


class PublishPostRequest(BaseModel):
    """Final request to publish post"""
    image_url: str
    caption: str
    platform: Literal["instagram", "facebook", "both"]
    schedule_time: Optional[str] = None  # For future scheduling feature