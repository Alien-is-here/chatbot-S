## This file is about using thoes tables
# Create chats , read chats , update chats , Delete chats (CURD) 

from typing import List , Optional # List[dict] -> function returns a list of items , Optional[str] -> value can be a string or None
from uuid import UUID  # type used for chat IDs ,  UUIDs -> Harder to guess, More secure , used in real apps

from sqlalchemy import select , update # This lets Python talk to the database.

from app.config import get_db_session # opens a safe connectio to db, do work and close it properly

from app.db.postgres.models import Chat, ChatStatus # chat -> table , ChatStatus -> the bitmask flag

def create_chat(user_id: int, title: Optional[str] = None, mode: Optional[str] = None) -> dict:
    """ Create a new chat """
    with get_db_session() as session:
        chat = Chat(
            user_id=user_id,
            title=title or "New Chat",
            mode=mode,
            state="IDLE"
        ) # Create a new chat for a user and return its info
        session.add(chat)
        session.flush()

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
    with get_db_session() as session:
        stmt = select(Chat).where(
            Chat.user_id == user_id,
            Chat.status.op("&")(ChatStatus.DELETED) == 0 , # 0 -> not deleted
            ).order_by(Chat.updated_at.desc())

        rows = session.execute(stmt).scalars().all() # stmt -> sends  query to PortgreSQL, scalars -> extract chat objects, all -> get all results as a list 

        return [
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

def get_chat(chat_id: UUID, user_id: int) -> Optional[dict]: # Opens one specific chat
    """Getting a specific chat"""
    with get_db_session() as session:
        stmt =  select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.status.op("&")(ChatStatus.DELETED) == 0,
        ) # User can ONLY open their own chats
        chat = session.execute(stmt).scalars().first()

        if not chat:
            return None # if chat doesnot exists return nothing

        return {
            "id": str(chat.id),
             "user_id": chat.user_id,
             "title": chat.title,
             "mode": chat.mode,
             "state": chat.state,
             "created_at": chat.created_at,
             "updated_at": chat.updated_at, 
        }

# ------------------------------------------ Updating Chat --------------------------------------------
def update_chat(
    chat_id: UUID,
    user_id: int,
    title: Optional[str] = None,
    state: Optional[str] = None,
    mode: Optional[str] = None
) -> Optional[dict]:
    """Update a chat"""
    with get_db_session() as session:
        # Build update values
        values = {} # creating empty update box
        if title is not None: # only updtae values that are provided (no overwriting)
            values["title"] = title
        if state is not None:
            values["state"] = state
        if mode is not None:
            values["mode"] = mode
        
        if not values:
            return get_chat(chat_id,user_id) # If nothing to update → just return current chat
        
        # update
        update_stmt = (
            update(Chat).where(Chat.id == chat_id , Chat.user_id == user_id)
            .values(**values) # unpack the dictionary
            .returning(Chat)
        )
        result = session.execute(update_stmt).scalars().first()
        session.flush()

        if not result:
            return None

        return {
            "id": str(result.id),
            "user_id": result.user_id,
            "title": result.title,
            "mode": result.mode,
            "state": result.state,
            "created_at": result.created_at,
            "updated_at": result.updated_at,
        }

# ------------------------------------------ Deleting Chat ----------------------------------------------------------------------------------------------
def delete_chat(chat_id: UUID, user_id: int) -> dict:
    """ Delete a chat"""
    with get_db_session() as session:
        #check if exists
        stmt = select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        chat = session.execute(stmt).scalars().first()

        if not chat:
            return {"chat_id": str(chat_id), "deleted":False}

        # set deleted chat
        update_stmt = (update(Chat).where(Chat.id == chat_id, Chat.user_id == user_id).values(status=Chat.status.op("|")(ChatStatus.DELETED))
        )

        session.execute(update_stmt)
        session.flush() # Force database to save changes now

        return {"chat_id": str(chat_id), "deleted": True}