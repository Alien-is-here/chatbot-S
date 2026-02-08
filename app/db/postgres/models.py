# This file models.py under postgres basically tells that these are the tables I want in my PostgreSQL database and this is what each table looks like

# Importing Toolkit
from sqlalchemy import{
    Column,
    Integar,
    String,
    DtaeTime,
    Text,
    Boolean,
    ForeignKey, # Link to another table
    JSON,
    func,       # current thing
    text
}

from sqlalchemy.dialects.postgresql import UUID     #PostgreSQL has a special UUID type (a v long , random ID)
from sqlalchemy.orm import declarative_base 

Base = declarative_base()   # Think of it as a base class

class ChatStatus: # Status Flags
    DELETED = 1
    ARCHIEVED = 2
    FLAGGED = 4

# =================================
# TABLE # 1: USERS
# =================================

class User(Base):
    __tablename__ = "users" # This creates a table named Users
    id = Column(Integar,primary_key=True) #Each user gets a unique id
    username = Column(String(255),unique=True, nullable=False) # Must exist, must be unique and max 255 characters
    email = Column(String(255),unique=True, nullable=False)


    # Optional info
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Firebase Integartion(-----)
    firebase_uid = Column(String(255), unique=True) # Links your db to Firebase user

    # Timestamps
    created_at = Column(DateTime(timezone=True),server_default=func.now()) # When user was created
    updated_at = Column(DateTime(timezone=True),server_default=func.now()) # When user was updtaed

    is_active = Column(Boolean, default=True)
    
# =====================================
# TABLE # 2: CHATS
# =====================================

class Chat(Base):
    __tablename__= "chats"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    ) # Database automatically creates a random ID. No two chats ever collide

    user_id = Column(Integar , ForeignKey("user_id"), nullable=False) # Means this chat belongs to one user
    title = Column(String(255)) # chat name
    state = Column(String(50),default="IDLE") # what bot is doing (Idle , Generating , Waiting)
    mode = Column(String(50))   # advertisement or general

    # Timestamps
    created_at = Column(DateTime(timezone=True),server_default=func.now()) # When chat was created
    updated_at = Column(DateTime(timezone=True),server_default=func.now()) # When chat was updtaed

    status = Column(Integar, default=0) # Chat status ( 0 -> normal, 1 -> deleted , 2 -> archived , 5 deleted + flagged)

# =====================================
# TABLE # 3: MESSAGES
# =====================================
class Message(Base):
    __tablename__ = "messages"

     id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Chat connection
    chat_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chats.id",onedelete="CASCADE"),
        NULLABLE=False
    )   # onedelete="CASCADE" -> if a chat is deletd--delete all its messages automatically

    role = Column(String(50)) # user or assistant ??
    content = Column(Text)  # Actual text message

    input = Column(JSON)
    output = Column(JSON)   # stores user inputs , model outputs , tokens , metadata, scores etc

    status = Column(String(50))

# =====================================
# TABLE # 3: POSTS
# =====================================

class Post(Base):
    __tablename__ ="posts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    user_id =Column(Integar , ForeignKey("users.id" , nullable=False))
    chat_id = Column(UUID(as_uuid=True, ForeignKey("chats.id", nullable=True)))

    # Product Advertisement Info
    product_name = Column(String(255))
    description = Column(Text)

    # Generated content
    image_url = Column(Text)
    image_filname = Column(String(255))
    caption = Column(Text)
    hashtags = Column(JSON , default=[])

    # Publishing Info
    platform = Column(String(50)) # insta , fb , both..
    status = Column(String(50), default="draft") # draft, published , failed

    # Social Media Post IDs

    post_id_instagram = Column(String(255)) # Social media Ids returned by FB/Inst API
    post_id_facebook = Column(String(255))

    # Timestamps
    craeted_at = Column(DtaeTime(timezone=True),server_default=func.now()) # When post was created
    published_at = Column(DtaeTime(timezone=True)) # When it was live
