from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config import get_settings
import os

load_dotenv()

settings = get_settings()

app = FastAPI(title= "Social Media Bot" , version="1.0.0")

# Initilizing OpenAI API key path
app = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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