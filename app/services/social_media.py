"""
services/social_media.py - Social Media Posting Service
========================================================
Handles posting to social media platforms:
- Instagram (via instagrapi)
- Facebook (via facebook-sdk)
"""

from instagrapi import Client as InstaClient
from instagrapi.exceptions import LoginRequired
import facebook
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from config import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstagramService:
    """
    Service for posting to Instagram using instagrapi.
    Uses private API (username/password login).
    """

    def __init__(self):
        """Initialize Instagram client"""
        self.settings = get_settings()
        self.client = None
        self._logged_in = False

    def login(self) -> bool:
        """
        Login to Instagram.

        Returns:
            True if login successful, False otherwise
        """
        if not self.settings.is_instagram_configured():
            logger.warning("⚠️  Instagram not configured")
            return False

        if self._logged_in:
            logger.info("✓ Already logged in to Instagram")
            return True

        try:
            logger.info("Logging in to Instagram...")

            self.client = InstaClient()
            self.client.login(
                self.settings.instagram_username,
                self.settings.instagram_password
            )

            self._logged_in = True
            logger.info("✓ Instagram login successful")
            return True

        except LoginRequired as e:
            logger.error(f"❌ Instagram login failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Instagram login error: {str(e)}")
            return False

    def post_photo(
            self,
            image_path: Path,
            caption: str,
            hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Post a photo to Instagram.

        Args:
            image_path: Path to image file
            caption: Post caption
            hashtags: List of hashtags (e.g., ["#fashion", "#style"])

        Returns:
            Dictionary with post results

        Example:
            result = instagram.post_photo(
                image_path=Path("product.jpg"),
                caption="Check out our new product!",
                hashtags=["#newproduct", "#sale"]
            )
        """
        # Ensure logged in
        if not self._logged_in:
            if not self.login():
                return {
                    "success": False,
                    "error": "Not logged in to Instagram"
                }

        try:
            # Build full caption with hashtags
            full_caption = caption
            if hashtags:
                # Add hashtags at the end
                hashtag_text = " ".join(hashtags)
                full_caption = f"{caption}\n\n{hashtag_text}"

            # Ensure caption is within Instagram limit (2,200 characters)
            if len(full_caption) > 2200:
                logger.warning("Caption too long, truncating...")
                full_caption = full_caption[:2197] + "..."

            logger.info(f"Posting to Instagram: {image_path.name}")

            # Upload photo
            media = self.client.photo_upload(
                path=str(image_path),
                caption=full_caption
            )

            result = {
                "success": True,
                "platform": "instagram",
                "media_id": media.id,
                "media_code": media.code,
                "url": f"https://www.instagram.com/p/{media.code}/",
                "caption_length": len(full_caption),
                "hashtag_count": len(hashtags) if hashtags else 0
            }

            logger.info(f"✓ Posted to Instagram: {result['url']}")
            return result

        except Exception as e:
            logger.error(f"❌ Instagram post failed: {str(e)}")
            return {
                "success": False,
                "platform": "instagram",
                "error": str(e)
            }

    def logout(self):
        """Logout from Instagram"""
        if self.client and self._logged_in:
            self.client.logout()
            self._logged_in = False
            logger.info("✓ Logged out from Instagram")


class FacebookService:
    """
    Service for posting to Facebook using Graph API.
    Requires Page Access Token.
    """

    def __init__(self):
        """Initialize Facebook Graph API client"""
        self.settings = get_settings()
        self.graph = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize Facebook Graph API.

        Returns:
            True if initialization successful
        """
        if not self.settings.is_facebook_configured():
            logger.warning("⚠️  Facebook not configured")
            return False

        if self._initialized:
            logger.info("✓ Facebook already initialized")
            return True

        try:
            logger.info("Initializing Facebook Graph API...")

            self.graph = facebook.GraphAPI(
                access_token=self.settings.facebook_access_token,
                version="3.0"
            )

            # Test the connection
            self.graph.get_object(self.settings.facebook_page_id)

            self._initialized = True
            logger.info("✓ Facebook Graph API initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Facebook initialization failed: {str(e)}")
            return False

    def post_photo(
            self,
            image_path: Path,
            message: str
    ) -> Dict[str, Any]:
        """
        Post a photo to Facebook page.

        Args:
            image_path: Path to image file
            message: Post message/caption

        Returns:
            Dictionary with post results

        Example:
            result = facebook.post_photo(
                image_path=Path("product.jpg"),
                message="Check out our new product! #newproduct"
            )
        """
        # Ensure initialized
        if not self._initialized:
            if not self.initialize():
                return {
                    "success": False,
                    "error": "Facebook not initialized"
                }

        try:
            logger.info(f"Posting to Facebook: {image_path.name}")

            # Open image file
            with open(image_path, 'rb') as image_file:
                # Upload photo to Facebook page
                response = self.graph.put_photo(
                    image=image_file,
                    message=message
                )

            result = {
                "success": True,
                "platform": "facebook",
                "post_id": response.get('id', ''),
                "message_length": len(message)
            }

            logger.info(f"✓ Posted to Facebook: {response.get('id', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"❌ Facebook post failed: {str(e)}")
            return {
                "success": False,
                "platform": "facebook",
                "error": str(e)
            }


class SocialMediaService:
    """
    Unified service for posting to multiple platforms.
    Manages Instagram and Facebook services.
    """

    def __init__(self):
        """Initialize all social media services"""
        self.settings = get_settings()
        self.instagram = InstagramService()
        self.facebook = FacebookService()

    def post_to_platforms(
            self,
            platforms: List[str],  # ["instagram", "facebook", "both"]
            image_path: Path,
            caption: str,
            hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Post to multiple platforms at once.

        Args:
            platforms: List of platforms ("instagram", "facebook", or "both")
            image_path: Path to image
            caption: Post caption/message
            hashtags: List of hashtags (for Instagram)

        Returns:
            Dictionary with results from each platform

        Example:
            result = social_media.post_to_platforms(
                platforms=["both"],
                image_path=Path("product.jpg"),
                caption="New product launch!",
                hashtags=["#newproduct", "#launch"]
            )
        """
        # Normalize platforms list
        if "both" in platforms:
            platforms = ["instagram", "facebook"]

        results = {
            "requested_platforms": platforms,
            "results": {},
            "overall_success": False
        }

        # Post to Instagram
        if "instagram" in platforms:
            if self.settings.instagram_enabled and self.settings.is_instagram_configured():
                logger.info("Posting to Instagram...")
                ig_result = self.instagram.post_photo(image_path, caption, hashtags)
                results["results"]["instagram"] = ig_result
            else:
                results["results"]["instagram"] = {
                    "success": False,
                    "error": "Instagram not configured or disabled"
                }

        # Post to Facebook
        if "facebook" in platforms:
            if self.settings.facebook_enabled and self.settings.is_facebook_configured():
                logger.info("Posting to Facebook...")

                # For Facebook, include hashtags in message
                fb_message = caption
                if hashtags:
                    fb_message = f"{caption}\n\n{' '.join(hashtags)}"

                fb_result = self.facebook.post_photo(image_path, fb_message)
                results["results"]["facebook"] = fb_result
            else:
                results["results"]["facebook"] = {
                    "success": False,
                    "error": "Facebook not configured or disabled"
                }

        # Check if at least one platform succeeded
        results["overall_success"] = any(
            r.get("success", False)
            for r in results["results"].values()
        )

        # Summary
        successful = [
            platform for platform, result in results["results"].items()
            if result.get("success", False)
        ]
        failed = [
            platform for platform, result in results["results"].items()
            if not result.get("success", False)
        ]

        results["summary"] = {
            "successful": successful,
            "failed": failed,
            "total_requested": len(platforms),
            "total_successful": len(successful),
            "total_failed": len(failed)
        }

        if results["overall_success"]:
            logger.info(f"✓ Posted to: {', '.join(successful)}")

        if failed:
            logger.warning(f"⚠️  Failed to post to: {', '.join(failed)}")

        return results

    def get_available_platforms(self) -> List[str]:
        """Get list of configured and enabled platforms"""
        return self.settings.get_enabled_platforms()


# ============================================
# SINGLETON INSTANCES
# ============================================

social_media_service = SocialMediaService()
instagram_service = InstagramService()
facebook_service = FacebookService()


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def post_to_platforms(*args, **kwargs):
    """Convenience function for multi-platform posting"""
    return social_media_service.post_to_platforms(*args, **kwargs)


def get_available_platforms():
    """Get list of available platforms"""
    return social_media_service.get_available_platforms()


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📱 Social Media Service Test")
    print("=" * 60)

    service = SocialMediaService()

    print(f"✓ Social Media Service initialized")

    available = service.get_available_platforms()
    print(f"\nAvailable platforms: {available if available else 'None configured'}")

    if "instagram" in available:
        print("  ✓ Instagram: Ready")
    else:
        print("  ❌ Instagram: Not configured")

    if "facebook" in available:
        print("  ✓ Facebook: Ready")
    else:
        print("  ❌ Facebook: Not configured")

    if not available:
        print("\n⚠️  No platforms configured!")
        print("Add credentials to .env:")
        print("  - INSTAGRAM_USERNAME & INSTAGRAM_PASSWORD")
        print("  - FACEBOOK_ACCESS_TOKEN & FACEBOOK_PAGE_ID")

    print("=" * 60 + "\n")