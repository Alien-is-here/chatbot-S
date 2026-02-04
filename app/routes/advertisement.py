from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_service import LLMService

router = APIRouter(prefix="/advertisement", tags=["Advertisement"])
llm_service = LLMService()


class ProductRequest(BaseModel):
    product_description: str
    style: str = "professional"  # professional, casual, creative
    platform: str = "instagram"  # instagram, facebook, both


class CaptionRequest(BaseModel):
    product_description: str
    image_url: Optional[str] = None
    platform: str = "instagram"
    tone: str = "professional"


class PostRequest(BaseModel):
    image_url: str
    caption: str
    platform: str  # instagram, facebook, both


@router.post("/generate-image")
async def generate_product_image(request: ProductRequest):
    """Step 1: Generate product image from description"""
    try:
        # Enhance prompt based on style
        enhanced_prompt = f"{request.product_description}, {request.style} photography style"

        image_url = await llm_service.generate_image(enhanced_prompt)

        return {
            "success": True,
            "image_url": image_url,
            "original_prompt": request.product_description,
            "enhanced_prompt": enhanced_prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-caption")
async def generate_caption(request: CaptionRequest):
    """Step 2: Generate post caption"""
    try:
        caption = await llm_service.generate_caption(
            product_description=request.product_description,
            platform=request.platform,
            tone=request.tone
        )

        return {
            "success": True,
            "caption": caption,
            "platform": request.platform,
            "character_count": len(caption)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_post(request: PostRequest):
    """Step 3: Preview before posting"""
    return {
        "success": True,
        "preview": {
            "image_url": request.image_url,
            "caption": request.caption,
            "platform": request.platform,
            "estimated_reach": "TBD"  # Can add analytics later
        }
    }


@router.post("/post")
async def post_to_social_media(request: PostRequest):
    """Step 4: Actually post to social media"""
    # This will be implemented in Phase 4
    return {
        "success": True,
        "message": "Posted successfully",
        "post_id": "generated_id",
        "platform": request.platform
    }