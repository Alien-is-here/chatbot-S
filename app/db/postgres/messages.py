from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update
from app.config import get_db_session
from app.db.postgres.models import Chat, Message

def create_message(
    chat_id: UUID,
    role: str,
    content: str,
    input_json: Optional[dict] = None,
    status: str = "completed"
    ) -> dict:
    """ Create a new message"""
    with get_db_session() as session:
        msg = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            input=input_json,
            status=status
        )
        session.add(msg)
        session.flush()

        return {
                "id": str(msg.id),
                "chat_id": str(msg.chat_id),
                "role": msg.role,
                "content": msg.content,
                "input": msg.input,
                "output": msg.output,
                "status": msg.status,
                "created_at": msg.created_at,
                "updated_at": msg.updated_at,
            }

# ------------------------------------------------ list Message ---------------------------------------------------
def list_messages(chat_id: UUID,user_id: int) -> List[dict]:
    """ Get all messages for a chat """
    with get_db_session() as session:
        stmt = ( 
            select(Message).join(Chat, Chat.id == Message.chat_id).where(Message.chat_id == chat_id , Chat.user_id == user_id).order_by(Message.created_at.asc())
        )
        rows = session.execute(stmt).scalars().all()
        return [
            {
                "id": str(r.id),
                "chat_id": str(r.chat_id),
                "role": r.role,
                "content": r.content,
                "input": r.input,
                "output": r.output,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in rows
        ]

# ------------------------------------------------ Get Message ---------------------------------------------------
def get_message(message_id: UUID, user_id: int) -> Optional[dict]:
    """Get a specific message"""
    with get_db_session() as session:
        stmt = (
            select(Message)
            .join(Chat, Chat.id == Message.chat_id)
            .where(Message.id == message_id, Chat.user_id == user_id)
        )
        msg = session.execute(stmt).scalars().first()
        
        if not msg:
            return None
        
        return {
            "id": str(msg.id),
            "chat_id": str(msg.chat_id),
            "role": msg.role,
            "content": msg.content,
            "input": msg.input,
            "output": msg.output,
            "status": msg.status,
            "created_at": msg.created_at,
        }


def update_message_output(
    message_id: UUID,
    output_json: Optional[dict],
    status: str = "completed"
    ) -> None:
        """Update message output"""
        with get_db_session() as session:
            stmt = (
                update(Message)
                .where(Message.id == message_id)
                .values(output=output_json, status=status)
            )
            session.execute(stmt)
            session.flush()
