from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.requests import GenerateCaptionRequest, PublishPostRequest
from app.models.responses import CaptionGenerationResponse, PostPublishResponse
from app.services.llm_service import LLMService
from app.services.image_service import ImageService
from app.services.social_media_service import SocialMediaService

router = APIRouter(prefix="/general", tags=["General Post Mode"])

llm_service = LLMService()
image_service = ImageService()
social_service = SocialMediaService()


@router.post("/upload-image")
async def upload_image(
        file: UploadFile = File(...),
        description: str = Form(None),
        should_analyze: bool = Form(True)
):
    """
    STEP 1 (General Flow): Upload existing image

    Flow:
    User uploads image → Validate → Save → Optionally analyze with GPT-4 Vision
    """
    # Read file content
    content = await file.read()

    # Validate image
    validation = await image_service.validate_image(content)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail=validation.get("error"))

    # Save image
    save_result = await image_service.save_image(content, file.filename)
    if not save_result.get("success"):
        raise HTTPException(status_code=500, detail=save_result.get("error"))

    response = {
        "success": True,
        "image_url": save_result["url"],
        "filename": save_result["filename"],
        "size": validation["size"],
        "dimensions": validation["dimensions"]
    }

    # Optional: Analyze image for caption generation help
    if should_analyze:
        analysis = await llm_service.analyze_and_describe_image(
            image_url=save_result["url"],
            purpose="caption_help"
        )
        if analysis.get("success"):
            response["image_analysis"] = analysis["analysis"]

    return response


@router.post("/generate-caption", response_model=CaptionGenerationResponse)
async def generate_general_caption(request: GenerateCaptionRequest):
    """
    STEP 2 (General Flow): Generate caption for general post

    Flow:
    Image analysis + user input → GPT-4 generates caption → Return caption
    """
    result