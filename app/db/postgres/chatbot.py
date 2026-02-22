# Brain 

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update # For Object Relational Mapping queries
from app.config import get_db_session
from app.db.postgres.models import Chat, Message, Post # ORM table models

# state dictionary
CONVERSATION_STATES = {
    "IDLE": "Waiting for user input",
    "MODE_SELECTION": "Choosing advertisement or general",
    "COLLECTING_PRODUCT_INFO": "Getting product details",
    "GENERATING_IMAGE": "AI generating image",
    "GENERATING_CAPTION": "AI generating caption",
    "PREVIEW": "Showing preview before publish",
    "PUBLISHING": "Publishing to social media",
    "COMPLETED": "Task completed"
}

# Keeps human read able meanings of internal chat states

def get_chat_context(chat_id: UUID, user_id: int) -> Optional[Dict[str,Any]]: # Returns chat metadata, recent messages, and associated post for a given user and chat.
     with get_db_session() as session:
        # Get chat
        chat_stmt = select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        chat = session.execute(chat_stmt).scalars().first()
        
        if not chat:
            return None
        
        # Get recent messages (last 10)
        msg_stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(10)
        )
        messages = session.execute(msg_stmt).scalars().all()
        
        # Get associated post (if any)
        post_stmt = select(Post).where(Post.chat_id == chat_id).order_by(Post.created_at.desc()).limit(1)
        post = session.execute(post_stmt).scalars().first()
        
        return {
            "chat_id": str(chat.id),
            "user_id": chat.user_id,
            "title": chat.title,
            "state": "IDLE",  # You can add a 'state' column to Chat model
            "messages": [
                {
                    "role": "user" if m.author_firebase_uid else "assistant",
                    "content": m.input.get("text", "") if m.input else "",
                    "created_at": m.created_at
                }
                for m in reversed(list(messages))
            ],
            "current_post": {
                "id": str(post.id),
                "mode": post.mode,
                "status": post.status,
                "description": post.description,
                "image_url": post.image_url,
                "caption": post.caption,
            } if post else None
        }

# ------------------- Updating Chat State ------------------------------------------------
def update_chat_state(chat_id: UUID, state: str, context_data: Optional[Dict] = None) -> bool:
     with get_db_session() as session:
        update_stmt = (
            update(Chat)
            .where(Chat.id == chat_id)
            .values(updated_at=datetime.now())
        )
        session.execute(update_stmt)
        session.flush()
        return True

# ----------------------- Getting Converstaion History ------------------------------------------------
def get_conversation_history(chat_id: UUID , limit: int = 10) -> List[Dict]:
     with get_db_session() as session:
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        messages = session.execute(stmt).scalars().all()
        
        history = []
        for msg in messages:
            # User message
            if msg.input:
                history.append({
                    "role": "user",
                    "content": msg.input.get("text", "")
                })
            # Assistant response
            if msg.output:
                history.append({
                    "role": "assistant",
                    "content": msg.output.get("text", "")
                })
        
        return history

# -------------------------------------------
def create_post(
    user_id: int,
    chat_id: Optional[UUID],
    mode: str,
    description: str,
    product_name: Optional[str] = None,
    platform: str = "instagram"
) -> dict:
    """Create a new post tied to a conversation"""
    with get_db_session() as session:
        post = Post(
            user_id=user_id,
            chat_id=chat_id,
            mode=mode,
            product_name=product_name,
            description=description,
            platform=platform,
            status="draft"
        )
        session.add(post)
        session.flush()
        
        return {
            "id": str(post.id),
            "user_id": post.user_id,
            "chat_id": str(post.chat_id) if post.chat_id else None,
            "mode": post.mode,
            "product_name": post.product_name,
            "description": post.description,
            "platform": post.platform,
            "status": post.status,
            "created_at": post.created_at,
        }


def update_post_content(
    post_id: UUID,
    image_url: Optional[str] = None,
    image_filename: Optional[str] = None,
    caption: Optional[str] = None,
    hashtags: Optional[List[str]] = None
) -> Optional[dict]:
    """Update AI-generated content for a post"""
    with get_db_session() as session:
        values = {}
        if image_url is not None:
            values["image_url"] = image_url
        if image_filename is not None:
            values["image_filename"] = image_filename
        if caption is not None:
            values["caption"] = caption
        if hashtags is not None:
            values["hashtags"] = hashtags
        
        if not values:
            return None
        
        update_stmt = (
            update(Post)
            .where(Post.id == post_id)
            .values(**values)
            .returning(Post)
        )
        result = session.execute(update_stmt).scalars().first()
        session.flush()
        
        if not result:
            return None
        
        return {
            "id": str(result.id),
            "image_url": result.image_url,
            "caption": result.caption,
            "hashtags": result.hashtags,
            "status": result.status,
        }


def update_post_status(
    post_id: UUID,
    status: str,
    post_id_instagram: Optional[str] = None,
    post_id_facebook: Optional[str] = None
) -> Optional[dict]:
    """Update post status after publishing"""
    with get_db_session() as session:
        values = {"status": status}
        
        if post_id_instagram:
            values["post_id_instagram"] = post_id_instagram
        if post_id_facebook:
            values["post_id_facebook"] = post_id_facebook
        if status == "published":
            values["published_at"] = datetime.now()
        
        update_stmt = (
            update(Post)
            .where(Post.id == post_id)
            .values(**values)
            .returning(Post)
        )
        result = session.execute(update_stmt).scalars().first()
        session.flush()
        
        if not result:
            return None
        
        return {
            "id": str(result.id),
            "status": result.status,
            "post_id_instagram": result.post_id_instagram,
            "post_id_facebook": result.post_id_facebook,
            "published_at": result.published_at,
        }


def get_post(post_id: UUID) -> Optional[dict]:
    """Get a specific post with all details"""
    with get_db_session() as session:
        stmt = select(Post).where(Post.id == post_id)
        post = session.execute(stmt).scalars().first()
        
        if not post:
            return None
        
        return {
            "id": str(post.id),
            "user_id": post.user_id,
            "chat_id": str(post.chat_id) if post.chat_id else None,
            "mode": post.mode,
            "product_name": post.product_name,
            "description": post.description,
            "image_url": post.image_url,
            "image_filename": post.image_filename,
            "caption": post.caption,
            "hashtags": post.hashtags,
            "platform": post.platform,
            "status": post.status,
            "post_id_instagram": post.post_id_instagram,
            "post_id_facebook": post.post_id_facebook,
            "created_at": post.created_at,
            "published_at": post.published_at,
        }


def get_chat_posts(chat_id: UUID) -> List[dict]:
    """Get all posts created in a specific chat/conversation"""
    with get_db_session() as session:
        stmt = (
            select(Post)
            .where(Post.chat_id == chat_id)
            .order_by(Post.created_at.desc())
        )
        rows = session.execute(stmt).scalars().all()
        
        return [
            {
                "id": str(r.id),
                "mode": r.mode,
                "product_name": r.product_name,
                "image_url": r.image_url,
                "caption": r.caption,
                "platform": r.platform,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in rows
        ]


def get_user_posts(user_id: int, limit: int = 20, status: Optional[str] = None) -> List[dict]:
    """Get all posts for a user, optionally filtered by status"""
    with get_db_session() as session:
        stmt = select(Post).where(Post.user_id == user_id)
        
        if status:
            stmt = stmt.where(Post.status == status)
        
        stmt = stmt.order_by(Post.created_at.desc()).limit(limit)
        
        rows = session.execute(stmt).scalars().all()
        
        return [
            {
                "id": str(r.id),
                "mode": r.mode,
                "product_name": r.product_name,
                "image_url": r.image_url,
                "caption": r.caption,
                "platform": r.platform,
                "status": r.status,
                "created_at": r.created_at,
                "published_at": r.published_at,
            }
            for r in rows
        ]

# ----------------- Getting user statistics ------------------------------------------------

def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Get user statistics (total chats, posts, published, etc.)"""
    with get_db_session() as session:
        # Count chats
        chat_count = session.execute(
            select(Chat).where(Chat.user_id == user_id)
        ).scalars().all()
        
        # Count posts by status
        posts = session.execute(
            select(Post).where(Post.user_id == user_id)
        ).scalars().all()
        
        return {
            "total_chats": len(chat_count),
            "total_posts": len(posts),
            "draft_posts": len([p for p in posts if p.status == "draft"]),
            "published_posts": len([p for p in posts if p.status == "published"]),
            "advertisement_posts": len([p for p in posts if p.mode == "advertisement"]),
            "general_posts": len([p for p in posts if p.mode == "general"]),
        }