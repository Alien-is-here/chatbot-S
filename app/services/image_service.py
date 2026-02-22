# This handles downloading , resizing  and saving images. It only processes images that only exists

from PIL import Image # Python Imaging Library
import requests     # Used to download images over HTTP/HTTPS.
from pathlib import Path # works cross-platform (Windows/Linux/Mac)
from typing import Optional, Tuple, Dict, Any
import logging  # info , warnings, errors
from io import BytesIO
import uuid
import sys
from app.config import get_settings # loads global app configuration


# Add parent directory to path so we can import config
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageService:
    """
    Service for image processing operations.
    Works independently of AI services - no API key required.
    """

    def __init__(self):
        """Initialize image service with config settings"""
        self.settings = get_settings()
        self.images_dir = self.settings.images_dir
        self.temp_dir = self.settings.temp_dir

# ------------------------------- Downloading Images ----------------------------------------------------


    def download_image(self, url: str, save_name: Optional[str] = None) -> Path:
       """ Example:
            path = image_service.download_image(
                "https://oaidalleapiprodscus.blob.core.windows.net/...",
                "product_nike_shoes.jpg"
            )
        """
        logger.info(f"Downloading image from: {url[:50]}...") # Logs first 50 characters

        try:
            # Download image
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Open image with PIL
            image = Image.open(BytesIO(response.content))

            # Generate filename if not provided
            if not save_name:
                save_name = f"img_{uuid.uuid4().hex[:8]}.jpg"

            # Ensure correct extension
            if not save_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                save_name += '.jpg'

            # Save to images directory
            save_path = self.images_dir / save_name

            # Convert RGBA to RGB if saving as JPEG
            if save_name.lower().endswith(('.jpg', '.jpeg')):
                if image.mode in ('RGBA', 'LA', 'P'): # (RGBA + Alpha, Grayscale + alpha , palette mode)
                    # Create the white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                else:
                    image = image.convert('RGB')

            # Save image
            image.save(save_path, quality=95, optimize=True)

            logger.info(f"Image is saved to: {save_path}")
            return save_path

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {str(e)}")
            raise Exception(f"Failed to download image: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            raise Exception(f"Failed to process image: {str(e)}")

# ------------------------------- Saving Images ----------------------------------------------------

    def save_uploaded_image(self, file_data: bytes, filename: str) -> Path:
        logger.info(f"Saving uploaded image: {filename}")

        try:
            # Open and validate image
            image = Image.open(BytesIO(file_data)) # File is in image forn not random bytes

            # Generate unique filename
            ext = Path(filename).suffix.lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                ext = '.jpg'

            save_name = f"upload_{uuid.uuid4().hex[:8]}{ext}"
            save_path = self.images_dir / save_name

            # Convert and save
            if ext in ['.jpg', '.jpeg']:
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                else:
                    image = image.convert('RGB')

            image.save(save_path, quality=95, optimize=True)

            logger.info(f"Uploaded image saved: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"Failed to save uploaded image: {str(e)}")
            raise Exception(f"Failed to save image: {str(e)}")

# ------------------------------- Resizing Images ----------------------------------------------------

    def resize_for_instagram(
        self,
        image_path: Path,
        aspect_ratio: str = "1:1"  # "1:1", "4:5", "16:9"
    ) -> Path:
       
        logger.info(f"Resizing image for Instagram ({aspect_ratio})")

        # Define target dimensions
        dimensions = {
            "1:1": (1080, 1080),
            "4:5": (1080, 1350),
            "16:9": (1080, 608)
        }

        target_size = dimensions.get(aspect_ratio, dimensions["1:1"])

        try:
            # Open image
            image = Image.open(image_path)

            # Calculate resize dimensions (maintain aspect ratio, then crop)
            img_ratio = image.width / image.height
            target_ratio = target_size[0] / target_size[1]

            if img_ratio > target_ratio:
                # Image is wider - resize based on height
                new_height = target_size[1]
                new_width = int(new_height * img_ratio)
            else:
                # Image is taller - resize based on width
                new_width = target_size[0]
                new_height = int(new_width / img_ratio)

            # Resize
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Center crop to target size
            left = (new_width - target_size[0]) // 2
            top = (new_height - target_size[1]) // 2
            right = left + target_size[0]
            bottom = top + target_size[1]

            image = image.crop((left, top, right, bottom))

            # Save resized image
            resized_path = self.temp_dir / f"resized_{image_path.name}"
            image.save(resized_path, quality=95, optimize=True)

            logger.info(f"Image resized to {target_size}")
            return resized_path

        except Exception as e:
            logger.error(f"Failed to resize image: {str(e)}")
            raise Exception(f"Failed to resize image: {str(e)}")


    def resize_for_facebook(self, image_path: Path) -> Path:

        logger.info("Resizing image for Facebook")

        target_size = (1200, 630)

        try:
            image = Image.open(image_path)

            # Calculate resize dimensions
            img_ratio = image.width / image.height
            target_ratio = target_size[0] / target_size[1]

            if img_ratio > target_ratio:
                new_height = target_size[1]
                new_width = int(new_height * img_ratio)
            else:
                new_width = target_size[0]
                new_height = int(new_width / img_ratio)

            # Resize and crop
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            left = (new_width - target_size[0]) // 2
            top = (new_height - target_size[1]) // 2
            right = left + target_size[0]
            bottom = top + target_size[1]

            image = image.crop((left, top, right, bottom))

            # Save
            resized_path = self.temp_dir / f"fb_{image_path.name}"
            image.save(resized_path, quality=95, optimize=True)

            logger.info("Image resized for Facebook")
            return resized_path

        except Exception as e:
            logger.error(f"Failed to resize for Facebook: {str(e)}")
            raise Exception(f"Failed to resize image: {str(e)}")

 # ------------------------------- Validating Images ----------------------------------------------------
    def validate_image(self, image_path: Path) -> Dict[str, Any]:
        try:
            image = Image.open(image_path)
            file_size = image_path.stat().st_size

            result = {
                "valid": True,
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": file_size,
                "size_mb": file_size / (1024 * 1024),
                "issues": []
            }

            # Check file size
            if file_size > self.settings.max_image_size:
                result["valid"] = False
                result["issues"].append(
                    f"File too large: {result['size_mb']:.2f}MB "
                    f"(max: {self.settings.max_image_size / (1024*1024):.1f}MB)"
                )

            # Check format
            if image.format.lower() not in self.settings.allowed_image_formats:
                result["valid"] = False
                result["issues"].append(
                    f"Unsupported format: {image.format} "
                    f"(allowed: {', '.join(self.settings.allowed_image_formats)})"
                )

            # Check minimum dimensions (Instagram requirement)
            if image.width < 320 or image.height < 320:
                result["valid"] = False
                result["issues"].append(
                    f"Image too small: {image.width}x{image.height} "
                    "(minimum: 320x320)"
                )

            if result["valid"]:
                logger.info(f"Image validation passed: {image.width}x{image.height}")
            else:
                logger.warning(f"Image validation failed: {', '.join(result['issues'])}")

            return result

        except Exception as e:
            logger.error(f"Image validation error: {str(e)}")
            return {
                "valid": False,
                "issues": [f"Failed to validate image: {str(e)}"]
            }

# ------------------------------- Information (Utilities) of Images ----------------------------------------------------

    def get_image_info(self, image_path: Path) -> Dict[str, Any]:
        # Get detailed information about an image
        try:
            image = Image.open(image_path)
            file_size = image_path.stat().st_size

            return {
                "filename": image_path.name,
                "path": str(image_path),
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Failed to get image info: {str(e)}")
            raise Exception(f"Failed to get image info: {str(e)}")

# ------------------------------- Cleaning----------------------------------------------------

    def cleanup_temp_files(self):
        # Delete all temporary files
        count = 0
        for file in self.temp_dir.glob("*"):
            if file.is_file():
                file.unlink()
                count += 1

        logger.info(f"✓ Cleaned up {count} temporary files")
        return count


# ------------------------------- Instance ----------------------------------------------------


image_service = ImageService()


# ------------------------------- Convenience Functions ----------------------------------------------------


def download_image(*args, **kwargs):
    # Convenience function for downloading images
    return image_service.download_image(*args, **kwargs)


def resize_for_instagram(*args, **kwargs):
    """Convenience function for Instagram resize"""
    return image_service.resize_for_instagram(*args, **kwargs)


def validate_image(*args, **kwargs):
    """Convenience function for image validation"""
    return image_service.validate_image(*args, **kwargs)


# ------------------------------- Testing Images ----------------------------------------------------

"""
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🖼️  Image Service Test")
    print("="*60)

    service = ImageService()

    print(f"✓ Image Service initialized")
    print(f"  Images directory: {service.images_dir}")
    print(f"  Temp directory: {service.temp_dir}")
    print(f"  Max file size: {service.settings.max_image_size / (1024*1024):.1f}MB")
    print(f"  Allowed formats: {', '.join(service.settings.allowed_image_formats)}")

    print("\n✓ Image service ready (no API key required)")
    print("  - Download images ✓")
    print("  - Resize images ✓")
    print("  - Validate images ✓")
    print("  - Process uploads ✓")

    print("="*60 + "\n") 
    """