"""
services/llm_services.py - AI/LLM Integration Service
======================================================
Handles all AI operations:
- Image generation using DALL-E
- Caption generation using GPT
- Image editing and enhancement
"""

from openai import OpenAI
from typing import Optional, Dict, Any
import logging
import base64
from pathlib import Path
import sys

# Add parent directory to path so we can import config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """
    Service class for AI operations using OpenAI API.
    Handles image generation, text generation, and image editing.
    """

    def __init__(self):
        """Initialize OpenAI client with API key from config"""
        self.settings = get_settings()

        # Initialize OpenAI client only if API key is available
        if self.settings.openai_api_key:
            self.client = OpenAI(api_key=self.settings.openai_api_key)
            logger.info("✓ OpenAI client initialized successfully")
        else:
            self.client = None
            logger.warning("⚠️  OpenAI API key not found. AI features disabled.")

    def _check_client(self):
        """Check if OpenAI client is initialized"""
        if not self.client:
            raise ValueError(
                "OpenAI API key not configured. "
                "Add OPENAI_API_KEY to your .env file."
            )

    # ============================================
    # IMAGE GENERATION
    # ============================================

    def generate_product_image(
        self,
        product_name: str,
        description: str,
        style: str = "professional product photography",
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a product image using DALL-E.

        Args:
            product_name: Name of the product
            description: Detailed description of the product
            style: Visual style (e.g., "professional", "minimalist", "vibrant")
            category: Product category (e.g., "clothing", "electronics")

        Returns:
            Dictionary containing:
                - url: URL of generated image
                - prompt: The prompt used
                - revised_prompt: OpenAI's revised version

        Example:
            result = llm_service.generate_product_image(
                product_name="Nike Air Max",
                description="Red and white sneakers with air cushioning",
                style="professional product photography",
                category="footwear"
            )
        """
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
            logger.error(f"❌ Image generation failed: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")

    def _build_image_prompt(
        self,
        product_name: str,
        description: str,
        style: str,
        category: Optional[str]
    ) -> str:
        """Build an optimized prompt for DALL-E"""

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

    # ============================================
    # CAPTION GENERATION
    # ============================================

    def generate_caption(
        self,
        content_type: str,  # "advertisement" or "general"
        content_info: Dict[str, Any],
        tone: str = "engaging",
        include_hashtags: bool = True,
        max_hashtags: int = 10
    ) -> Dict[str, Any]:
        """
        Generate a social media caption using GPT.

        Args:
            content_type: Type of content ("advertisement" or "general")
            content_info: Dictionary with content details
                For ads: {product_name, description, category, price}
                For general: {topic, message, target_audience}
            tone: Desired tone (engaging, professional, casual, excited)
            include_hashtags: Whether to include hashtags
            max_hashtags: Maximum number of hashtags

        Returns:
            Dictionary containing:
                - caption: Generated caption text
                - hashtags: List of hashtags
                - emoji_count: Number of emojis used

        Example:
            result = llm_service.generate_caption(
                content_type="advertisement",
                content_info={
                    "product_name": "Nike Air Max",
                    "description": "Comfortable running shoes",
                    "category": "footwear",
                    "price": "$120"
                },
                tone="exciting"
            )
        """
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

            logger.info(f"✓ Caption generated: {len(caption)} chars, {len(hashtags)} hashtags")
            return result

        except Exception as e:
            logger.error(f"❌ Caption generation failed: {str(e)}")
            raise Exception(f"Failed to generate caption: {str(e)}")

    def _build_caption_prompt(
        self,
        content_type: str,
        content_info: Dict[str, Any],
        tone: str,
        include_hashtags: bool,
        max_hashtags: int
    ) -> str:
        """Build prompt for caption generation"""

        if content_type == "advertisement":
            prompt = f"""
Create an engaging Instagram/Facebook caption for this product:

Product Name: {content_info.get('product_name', 'N/A')}
Description: {content_info.get('description', 'N/A')}
Category: {content_info.get('category', 'N/A')}
Price: {content_info.get('price', 'N/A')}

Tone: {tone}
"""
        else:  # general post
            prompt = f"""
Create an engaging Instagram/Facebook caption for:

Topic: {content_info.get('topic', 'N/A')}
Message: {content_info.get('message', 'N/A')}
Target Audience: {content_info.get('target_audience', 'general')}

Tone: {tone}
"""

        # Add guidelines
        prompt += f"""

Requirements:
- Write a compelling caption that encourages engagement
- Use emojis naturally (2-5 emojis)
- Keep it under 2000 characters
- Make it conversational and authentic
"""

        if include_hashtags:
            prompt += f"\n- Include {max_hashtags} relevant hashtags at the end"
        else:
            prompt += "\n- Do not include hashtags"

        return prompt

    def _parse_caption_response(
        self,
        text: str,
        include_hashtags: bool
    ) -> tuple[str, list[str]]:
        """Parse caption text and extract hashtags"""

        if not include_hashtags:
            return text.strip(), []

        # Split by lines to find hashtags
        lines = text.strip().split('\n')

        caption_lines = []
        hashtags = []

        for line in lines:
            line = line.strip()
            # If line starts with # or contains multiple #, treat as hashtag line
            if line.startswith('#') or line.count('#') > 2:
                # Extract all hashtags from this line
                tags = [word for word in line.split() if word.startswith('#')]
                hashtags.extend(tags)
            else:
                caption_lines.append(line)

        caption = '\n'.join(caption_lines).strip()

        return caption, hashtags

    # ============================================
    # IMAGE EDITING
    # ============================================

    def edit_image(
        self,
        image_path: Path,
        edit_instruction: str
    ) -> Dict[str, Any]:
        """
        Edit an existing image using OpenAI's image edit endpoint.

        Args:
            image_path: Path to the image file
            edit_instruction: What to change (e.g., "make background white")

        Returns:
            Dictionary with edited image URL

        Note: This requires the image to be PNG with transparency.
        For basic edits, use image_service.py instead.
        """
        self._check_client()

        logger.info(f"Editing image: {image_path}")

        try:
            # Read image file
            with open(image_path, 'rb') as image_file:
                # Call image edit API
                response = self.client.images.edit(
                    image=image_file,
                    prompt=edit_instruction,
                    size=self.settings.image_size,
                    n=1
                )

            result = {
                "url": response.data[0].url,
                "prompt": edit_instruction,
                "success": True
            }

            logger.info("✓ Image edited successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Image editing failed: {str(e)}")
            raise Exception(f"Failed to edit image: {str(e)}")

    # ============================================
    # CONTENT ENHANCEMENT
    # ============================================

    def enhance_description(
        self,
        original_description: str,
        enhancement_type: str = "expand"
    ) -> str:
        """
        Enhance a product/post description.

        Args:
            original_description: Original text
            enhancement_type: "expand", "simplify", or "professional"

        Returns:
            Enhanced description text
        """
        self._check_client()

        prompts = {
            "expand": "Expand this description with more details and benefits:",
            "simplify": "Simplify this description to be more concise:",
            "professional": "Rewrite this in a professional marketing tone:"
        }

        prompt = f"{prompts.get(enhancement_type, prompts['expand'])}\n\n{original_description}"

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a professional copywriter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            enhanced = response.choices[0].message.content.strip()
            logger.info("✓ Description enhanced")
            return enhanced

        except Exception as e:
            logger.error(f"❌ Enhancement failed: {str(e)}")
            raise Exception(f"Failed to enhance description: {str(e)}")


# ============================================
# SINGLETON INSTANCE
# ============================================

# Create a single instance to be reused
llm_service = LLMService()


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def generate_product_image(*args, **kwargs):
    """Convenience function for image generation"""
    return llm_service.generate_product_image(*args, **kwargs)


def generate_caption(*args, **kwargs):
    """Convenience function for caption generation"""
    return llm_service.generate_caption(*args, **kwargs)


def edit_image(*args, **kwargs):
    """Convenience function for image editing"""
    return llm_service.edit_image(*args, **kwargs)


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 LLM Service Test")
    print("="*60)

    service = LLMService()

    if service.client:
        print("✓ OpenAI client initialized")
        print("\nTest: Generate product image (commented out - requires API credits)")
        print("Test: Generate caption (commented out - requires API credits)")

        # Uncomment to test when you have API key:
        # result = service.generate_caption(
        #     content_type="advertisement",
        #     content_info={
        #         "product_name": "Test Product",
        #         "description": "A great product",
        #         "category": "Test"
        #     }
        # )
        # print(f"Caption: {result['caption']}")
    else:
        print("❌ OpenAI client not initialized (API key missing)")
        print("Add OPENAI_API_KEY to .env to enable AI features")

    print("="*60 + "\n")