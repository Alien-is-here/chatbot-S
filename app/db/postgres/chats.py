## This file is about using thoes tables
# Create chats , read chats , update chats , Delete chats (CURD) 

from typing import List , Optional # List[dict] -> function returns a list of items , Optional[str] -> value can be a string or None
from uuid import UUID type used for chat IDs

from sqlalchemy import select , update

from app.config import get_db_session # opens a safe connectio to db, do work and close it properly

from app.db.portgres.models import Chat , ChatStatus # caht -> table , ChatStatus -> the bitmask flag

def create_chat(user_id: int, title: Optional[str] = None, mode: Optional[str] = None) -> dict:
    """ Create a new chat """
    chat = Chat(
        user_id=user_id,
        title=title or "New Chat"
        mode=mode,
        state="IDLE"
    ) # Create a new chat for a user and return its info

    return {
        "id": str(chat.id),
        "user_id": chat.user_id,
        "title": chat.title,
        "mode": chat.mode,
        "state": chat.state,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
    } # converting db objects into dict


def list_chats(user_id: int) -> List[dict]: # Takes user id and returns a list of chats
    """ Get all non - deleted chats for a user """
    with get_db_session() as sessiom:
        stmt = select(Chat).where(
            Chat.user_id == user_id,
            Chat.status.op("&")(ChatStatus.DELETED) == 0 , # 0 -> not deleted
            ).order_by(Chat.updated_at.desc())

        rows = session.exeute(stmt).scalars().all() # stmt -> sends  query to PortgreSQL, scalars -> extract chat objects, all -> get all results as a list 

        retuen [
            {
            "id": str(r.id),
             "user_id": r.user_id,
             "title": r.title,
             "mode": r.mode,
             "state": r.state,
             "created_at": r.created_at,
             "updated_at": r.updated_at,    
            }
            for r in rows
        ] # JSON friendly -> For every chat object r , make a dictionary