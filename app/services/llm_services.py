# This file generates product images and captions with hashtags
from openai import OpenAI
from typing import Optional, Dict, Any
import logging
import base64
from pathlib import Path
import sys
from app.config import get_settings

# Add parent directory to path so we can import config
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self):
        """Initialize OpenAI client with API key from config"""
        self.settings = get_settings()

        # Initialize OpenAI client only if API key is available
        if self.settings.openai_api_key:
            self.client = OpenAI(api_key=self.settings.openai_api_key)
            logger.info("OpenAI client initialized successfully")
        else:
            self.client = None
            logger.warning("OpenAI API key not found. AI features disabled.")

# ------------------------- Enhancing user prompt -----------------------------------------------
def enhance_user_prompt(self, product_description: str , style:str ) -> str:
    user_message = f"Prduct: {product_description}\nStyle: {style}"
    response = self.client.chat.completions.cretae(
        model=self.settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user" , "content": user_message}
        ],
        max_tokens = 30
    )
    return reponse.choices[0].message.content.strip()
 
 # ----------------------- Generating Image -----------------------------------

    def generate_product_image(
        self,
        product_name: str,
        description: str,
        style: str = "professional product photography",
        category: Optional[str] = None
    ) -> Dict[str, Any]:
      
        self._check_client()

        # Build the prompt
        prompt = self._build_image_prompt(
            product_name, description, style, category
        )

        logger.info(f"Generating image with prompt: {prompt[:100]}...")

        try:
            # Call DALL-E API
            response = self.client.images.generate(
                model=self.settings.dalle_model,
                prompt=prompt,
                size=self.settings.image_size,
                quality=self.settings.image_quality,
                n=1  # Generate 1 image
            )

            # Extract result
            image_data = response.data[0]

            result = {
                "url": image_data.url,
                "prompt": prompt,
                "revised_prompt": image_data.revised_prompt,
                "success": True
            }

            logger.info(f"✓ Image generated successfully")
            return result

        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")


    def _build_image_prompt(
        self,
        product_name: str,
        description: str,
        style: str,
        category: Optional[str]
    ) -> str:

        prompt_parts = [
            f"Create a {style} image of {product_name}.",
            f"Product details: {description}."
        ]

        if category:
            prompt_parts.append(f"Category: {category}.")

        # Add style guidelines
        prompt_parts.extend([
            "The image should be:",
            "- High quality and professional",
            "- Well-lit with good contrast",
            "- Centered composition",
            "- Clean background",
            "- Suitable for social media marketing"
        ])

        return " ".join(prompt_parts)

   # ----------------------- Generating Caption -----------------------------------
    def generate_caption(
        self,
        content_type: str,  # "advertisement" or "general"
        content_info: Dict[str, Any],
        tone: str = "engaging",
        include_hashtags: bool = True,
        max_hashtags: int = 10
    ) -> Dict[str, Any]:
    
        self._check_client()

        # Build the prompt for caption generation
        prompt = self._build_caption_prompt(
            content_type, content_info, tone, include_hashtags, max_hashtags
        )

        logger.info(f"Generating caption for {content_type}...")

        try:
            # Call GPT API
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional social media content creator. "
                            "Create engaging, authentic captions that drive engagement. "
                            "Use emojis naturally and include relevant hashtags."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,  # Creative but not too random
                max_tokens=500
            )

            # Extract the generated caption
            full_text = response.choices[0].message.content.strip()

            # Parse caption and hashtags
            caption, hashtags = self._parse_caption_response(
                full_text, include_hashtags
            )

            # Count emojis (simple check for common emoji ranges)
            emoji_count = sum(
                1 for char in caption
                if ord(char) > 127000  # Simplified emoji detection
            )

            result = {
                "caption": caption,
                "hashtags": hashtags,
                "full_text": full_text,
                "emoji_count": emoji_count,
                "character_count": len(caption),
                "success": True
            }

            logger.info(f"Caption generated: {len(caption)} chars, {len(hashtags)} hashtags")
            return result

        except Exception as e:
            logger.error(f"Caption generation failed: {str(e)}")
            raise Exception(f"Failed to generate caption: {str(e)}")

   # ----------------------- Coversational Messages -----------------------------------
 
 def chat(self, messages: list, system_prompt: str = None) -> str:
        """
        The chatbot brain — takes conversation history → returns next reply.

        messages = [
            {"role": "user", "content": "I want to sell clothes"},
            {"role": "assistant", "content": "Great! What product?"},
            {"role": "user", "content": "A red dress"}
        ]
        """
        all_messages = []

        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})

        all_messages.extend(messages)

        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=all_messages,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()


# Singleton — one instance shared across the app
llm_service = LLMService()