# This file for logging etc
# Generating Unique error codes for debugging

import hashlib # Python special library for hashing data
from datetime import datetime , timezone
from typing import Any , Dict , Optional
from pymongo.collection import Collection # represents mongovd collection -> This allows function signatures

# ----------------------------------    -----------------------------------
def generate_error_code(stage: str , error_message: str) -> str: # This helps map an error uniquely to a stage + message combination.
    content = f"{stage}:{error_message}"
    hash_obj = hashlib.sha256(content.encode()) # Guarantees that the same stage + message always produces the same hash, useful for consistent error codes.
    return hash_obj.hexdigest()[:8].upper() # Even if the error message is long, this gives a fixed-length identifier

# ----------------------------------    -----------------------------------

def get_user_friendly_error(stage: str) -> str: # Converts internal error stages into user-friendly messages

    error_map = {
        # Image generation stages
       image_generation": "Failed to generate image. Please try again.",
        "image_upload": "Failed to upload image. Please check the file.",
        "image_processing": "Failed to process image.",
        
        # Caption generation stages
        "caption_generation": "Failed to generate caption. Please try again.",
        
        # Publishing stages
        "instagram_publish": "Failed to post to Instagram. Check your credentials.",
        "facebook_publish": "Failed to post to Facebook. Check your credentials.",
        "social_media_publish": "Failed to publish post.",
        
        # Conversation stages
        "chat_processing": "Failed to process your message.",
        "mode_selection": "Failed to understand mode selection.",
        
        # General
        "unknown": "Something went wrong. Please try again.",
    }
    return error_map.get(stage, "Failed to process your request.")

# ----------------------------------    -----------------------------------
def log_conversation(
     mongo_client: Optional[Collection],
    user_id: int,
    chat_id: str,
    message: str,
    response: str,
    stage: str = "conversation",
    metadata: Optional[Dict] = None
    ) -> None: # Store a user message + bot response in MongoDB

     if mongo_client is None:
        print("MongoDB not available. Skipping conversation log.")
        return
    
    document = {
        "type": "conversation",
        "timestamp": datetime.now(timezone.utc),
        "user_id": user_id,
        "chat_id": chat_id,
        "stage": stage,
        "user_message": message,
        "bot_response": response,
        "metadata": metadata or {}
    } # log entry
    
    try:
        result = mongo_client.insert_one(document)
        print(f"Conversation logged: {result.inserted_id}")
    except Exception as e:
        print(f"Failed to log conversation: {e}")

# ----------------------------------    -----------------------------------
def log_image_generation(
    mongo_client: Optional[Collection],
    user_id: int,
    chat_id: str,
    prompt: str,
    enhanced_prompt: str,
    image_url: Optional[str] = None,
    generation_time: Optional[float] = None,
    error: Optional[str] = None,
    model: str = ""
    ) -> Optional[str];

    if mongo_client is None:
        print("MongoDB not available. Skipping image generation log.")
        return None

    error_code = None
    if error:
        error_code = generate_error_code("image_generation",error)
    
    document = {
        "type": "image_generation",
        "timestamp": datetime.now(timezone.utc),
        "user_id": user_id,
        "chat_id": chat_id,
        "prompt": prompt,
        "enhanced_prompt": enhanced_prompt,
        "image_url": image_url,
        "model": model,
        "generation_time_seconds": generation_time,
        "success": error is None,
        "error": error,
        "error_code": error_code
    }

    try:
        result = mongo_client.insert_one(document)
        print(f" Image generation logged: {result.inserted_id}")
        return generate_error_code
    expect Exception as e:
        print(f" Failed to log image generation: {e}")
        return error_code

# ----------------------------------    -----------------------------------
def log_caption_generation(
    mongo_client: Optional[Collection],
    user_id: int,
    chat_id: str,
    product_description: str,
    generated_caption: Optional[str] = None,
    hashtags: Optional[list] = None,
    generation_time: Optional[float] = None,
    error: Optional[str] = None,
    model: str = "gpt-4"
    ) -> Optional[str]:

     if mongo_client is None:
        print("MongoDB not available. Skipping caption generation log.")
        return None
    
    error_code = None
    if error:
        error_code = generate_error_code("caption_generation", error)
    
    document = {
        "type": "caption_generation",
        "timestamp": datetime.now(timezone.utc),
        "user_id": user_id,
        "chat_id": chat_id,
        "product_description": product_description,
        "generated_caption": generated_caption,
        "hashtags": hashtags or [],
        "hashtag_count": len(hashtags) if hashtags else 0,
        "caption_length": len(generated_caption) if generated_caption else 0,
        "model": model,
        "generation_time_seconds": generation_time,
        "success": error is None,
        "error": error,
        "error_code": error_code
    }
    
    try:
        result = mongo_client.insert_one(document)
        print(f"Caption generation logged: {result.inserted_id}")
        return error_code
    except Exception as e:
        print(f"Failed to log caption generation: {e}")
        return error_code


# ----------------------------------    -----------------------------------
def log_post_publish(
    mongo_client: Optional[Collection],
    user_id: int,
    post_id: str,
    platform: str,
    success: bool,
    post_url: Optional[str] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict] = None
    ) -> Optional[str]:

    if mongo_client is None:
        print("MongoDB not available. Skipping publish log.")
        return None
    
    error_code = None
    if error:
        stage = f"{platform}_publish"
        error_code = generate_error_code(stage, error)
    
    document = {
        "type": "post_publish",
        "timestamp": datetime.now(timezone.utc),
        "user_id": user_id,
        "post_id": post_id,
        "platform": platform,
        "success": success,
        "post_url": post_url,
        "error": error,
        "error_code": error_code,
        "metadata": metadata or {}
    }
    
    try:
        result = mongo_client.insert_one(document)
        print(f"✓ Post publish logged: {result.inserted_id}")
        return error_code
    except Exception as e:
        print(f"✗ Failed to log post publish: {e}")
        return error_code

# ----------------------------------    -----------------------------------
def log_error(
    mongo_client: Optional[Collection],
    stage: str,
    error_message: str,
    user_id: Optional[int] = None,
    chat_id: Optional[str] = None,
    **kwargs: Any
    ) -> Optional[str]:

    if mongo_client is None:
        print("MongoDB not available. Skipping error log.")
        return None
    
    error_code = generate_error_code(stage, error_message)
    user_friendly_msg = get_user_friendly_error(stage)
    
    document = {
        "type": "error",
        "timestamp": datetime.now(timezone.utc),
        "stage": stage,
        "error_message": error_message,
        "error_code": error_code,
        "user_friendly_message": user_friendly_msg,
        "user_id": user_id,
        "chat_id": chat_id,
        **kwargs
    }
    
    try:
        result = mongo_client.insert_one(document)
        print(f"Error logged [{error_code}]: {result.inserted_id}")
        return error_code
    except Exception as e:
        print(f"Failed to log error: {e}")
        return error_code

# ----------------------------------    -----------------------------------
def get_user_analytics(
    mongo_client: Optional[Collection],
    user_id: int,
    days: int = 30
    ) -> Optional[Dict]:

     if mongo_client is None:
        return None
    
    from datetime import timedelta
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    try:
        # Count different types of logs
        total_conversations = mongo_client.count_documents({
            "type": "conversation",
            "user_id": user_id,
            "timestamp": {"$gte": cutoff_date}
        })
        
        total_images = mongo_client.count_documents({
            "type": "image_generation",
            "user_id": user_id,
            "timestamp": {"$gte": cutoff_date}
        })
        
        successful_images = mongo_client.count_documents({
            "type": "image_generation",
            "user_id": user_id,
            "success": True,
            "timestamp": {"$gte": cutoff_date}
        })
        
        total_posts = mongo_client.count_documents({
            "type": "post_publish",
            "user_id": user_id,
            "timestamp": {"$gte": cutoff_date}
        })
        
        successful_posts = mongo_client.count_documents({
            "type": "post_publish",
            "user_id": user_id,
            "success": True,
            "timestamp": {"$gte": cutoff_date}
        })

        return {
            "user_id": user_id,
            "period_days": days,
            "total_conversations": total_conversations,
            "total_images_generated": total_images,
            "successful_images": successful_images,
            "image_success_rate": (successful_images / total_images * 100) if total_images > 0 else 0,
            "total_posts": total_posts,
            "successful_posts": successful_posts,
            "post_success_rate": (successful_posts / total_posts * 100) if total_posts > 0 else 0,
        }
         except Exception as e:
        print(f"✗ Failed to get analytics: {e}")
        return None