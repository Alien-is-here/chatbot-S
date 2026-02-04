from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
import os

settings = get_settings()

app = FastAPI(title= "Social Media Bot" , version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Social Media Bot is running",
            "environment": settings.app_env}