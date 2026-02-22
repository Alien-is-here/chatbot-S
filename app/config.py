
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from typing import List, Optional
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for automatic validation and type checking.
    """

    # ============================================
    # OPENAI CONFIGURATION
    # ============================================
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key for GPT and DALL-E")
    openai_model: str = Field(default="gpt-4o", description="GPT model to use")
    dalle_model: str = Field(default="dall-e-3", description="DALL-E model for image generation")
    image_size: str = Field(default="1024x1024", description="Generated image size")
    image_quality: str = Field(default="standard", description="Image quality: standard or hd")

    # ============================================
    # INSTAGRAM CONFIGURATION
    # ============================================
    # Note: Instagram Graph API requires Business/Creator account
    instagram_username: Optional[str] = Field(default=None, description="Instagram username")
    instagram_password: Optional[str] = Field(default=None, description="Instagram password")
    instagram_access_token: Optional[str] = Field(default=None, description="Instagram Graph API token")
    instagram_account_id: Optional[str] = Field(default=None, description="Instagram Business Account ID")
    instagram_enabled: bool = Field(default=True, description="Enable Instagram posting")

    # ============================================
    # FACEBOOK CONFIGURATION
    # ============================================
    facebook_access_token: Optional[str] = Field(default=None, description="Facebook Page Access Token")
    facebook_page_id: Optional[str] = Field(default=None, description="Facebook Page ID")
    facebook_enabled: bool = Field(default=True, description="Enable Facebook posting")

    # ============================================
    # APPLICATION SETTINGS
    # ============================================
    app_name: str = Field(default="AI Social Media Bot", description="Application name")
    app_env: str = Field(default="development", description="Environment: development or production")
    debug: bool = Field(default=True, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # ============================================
    # IMAGE PROCESSING SETTINGS
    # ============================================
    max_image_size: int = Field(default=5242880, description="Max image size in bytes (5MB)")
    allowed_image_formats: List[str] = Field(
        default=["jpg", "jpeg", "png", "webp"],
        description="Allowed image formats"
    )

    # ============================================
    # PATHS
    # ============================================
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent)

    @property
    def static_dir(self) -> Path:
        """Directory for static files"""
        return self.base_dir / "static"

    @property
    def images_dir(self) -> Path:
        """Directory for storing images"""
        path = self.static_dir / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def temp_dir(self) -> Path:
        """Directory for temporary files"""
        path = self.static_dir / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def logs_dir(self) -> Path:
        """Directory for log files"""
        path = self.base_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ============================================
    # VALIDATION
    # ============================================
    @field_validator('allowed_image_formats', mode='before')
    @classmethod
    def parse_formats(cls, v):
        """Parse comma-separated string or list"""
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(',')]
        return [fmt.lower() for fmt in v]

    @field_validator('image_size')
    @classmethod
    def validate_image_size(cls, v):
        """Validate image size format"""
        valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        if v not in valid_sizes:
            raise ValueError(f"Image size must be one of: {valid_sizes}")
        return v

    @field_validator('image_quality')
    @classmethod
    def validate_image_quality(cls, v):
        """Validate image quality"""
        if v not in ["standard", "hd"]:
            raise ValueError("Image quality must be 'standard' or 'hd'")
        return v

    # ============================================
    # HELPER METHODS
    # ============================================
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"

    def is_instagram_configured(self) -> bool:
        """Check if Instagram is properly configured"""
        # For instagrapi (private API)
        if self.instagram_username and self.instagram_password:
            return True
        # For Graph API (business accounts)
        if self.instagram_access_token and self.instagram_account_id:
            return True
        return False

    def is_facebook_configured(self) -> bool:
        """Check if Facebook is properly configured"""
        return bool(self.facebook_access_token and self.facebook_page_id)

    def get_enabled_platforms(self) -> List[str]:
        """Get list of enabled and configured platforms"""
        platforms = []
        if self.instagram_enabled and self.is_instagram_configured():
            platforms.append("instagram")
        if self.facebook_enabled and self.is_facebook_configured():
            platforms.append("facebook")
        return platforms

    # ============================================
    # PYDANTIC SETTINGS CONFIG
    # ============================================
    class Config:
        env_file = ".env"  # Look for .env in same directory as config.py
        env_file_encoding = "utf-8"
        case_sensitive = False  # Allow both OPENAI_API_KEY and openai_api_key
        extra = "ignore"  # Ignore extra fields in .env file


# ============================================
# SINGLETON PATTERN
# ============================================
@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure Settings is only loaded once.
    """
    return Settings()


# ============================================
# CONVENIENCE ACCESSOR
# ============================================
# This allows you to import settings directly
settings = get_settings()


# ============================================
# CONFIGURATION SUMMARY
# ============================================
def print_config_summary():
    """Print configuration summary for debugging"""
    s = get_settings()

    print("\n" + "="*60)
    print(f"🤖 {s.app_name}")
    print("="*60)
    print(f"🌍 Environment: {s.app_env}")
    print(f"🔧 Debug Mode: {s.debug}")
    print(f"🌐 Server: {s.host}:{s.port}")
    print(f"📍 Base Directory: {s.base_dir}")

    print(f"\n🤖 AI Services:")
    if s.openai_api_key:
        print(f"  ✓ OpenAI API: Configured")
        print(f"  └─ Model: {s.openai_model}")
        print(f"  └─ DALL-E: {s.dalle_model}")
    else:
        print(f"  ❌ OpenAI API: NOT CONFIGURED (Add OPENAI_API_KEY to .env)")
        print(f"  ⚠️  AI features will not work without API key!")

    print(f"\n📱 Social Media Platforms:")
    platforms = s.get_enabled_platforms()

    print(f"  {'✓' if 'instagram' in platforms else '❌'} Instagram: ", end="")
    if 'instagram' in platforms:
        print("Enabled & Configured")
        if s.instagram_username:
            print(f"    └─ Method: Private API (instagrapi)")
        else:
            print(f"    └─ Method: Graph API")
    else:
        print("Not configured or disabled")

    print(f"  {'✓' if 'facebook' in platforms else '❌'} Facebook: ", end="")
    if 'facebook' in platforms:
        print("Enabled & Configured")
    else:
        print("Not configured or disabled")

    print(f"\n📁 Directories:")
    print(f"  Images: {s.images_dir}")
    print(f"  Temp: {s.temp_dir}")
    print(f"  Logs: {s.logs_dir}")

    print(f"\n🖼️  Image Settings:")
    print(f"  Size: {s.image_size}")
    print(f"  Quality: {s.image_quality}")
    print(f"  Max Size: {s.max_image_size / 1024 / 1024:.1f} MB")
    print(f"  Formats: {', '.join(s.allowed_image_formats)}")

    print("="*60 + "\n")


# ============================================
# RUN ON IMPORT (DEBUG MODE ONLY)
# ============================================
if __name__ == "__main__":
    # Test configuration
    print_config_summary()

    # Test settings access
    s = get_settings()
    print(f"Testing settings access:")
    print(f"OpenAI Key (first 10 chars): {s.openai_api_key[:10]}...")
    print(f"Enabled platforms: {s.get_enabled_platforms()}")

# ============================================
# DATABASE CONFIGURATION
# ============================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

# Build the PostgreSQL connection URL from your .env file
# Think of this like the restaurant's address so the waiter knows where the kitchen is
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/chatbot_db"  # default fallback
)

# Engine = the actual connection to PostgreSQL (like opening the kitchen door)
engine = create_engine(DATABASE_URL, echo=settings.debug)

# SessionLocal = a factory that creates database sessions (like giving a waiter their notepad)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Session:
    """
    Safe database session.
    Think of it like: open notepad → do work → save and close notepad.
    If anything goes wrong → throw away the notepad (rollback).
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()   # Save all changes to database
    except Exception:
        session.rollback() # Something went wrong → undo everything
        raise
    finally:
        session.close()    # Always close the connection when done
```

Also add this to your `.env` file:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/chatbot_db