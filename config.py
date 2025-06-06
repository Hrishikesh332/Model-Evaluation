import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())
    UPLOAD_FOLDER = 'uploads'
    VIDEO_FOLDER = 'videos'
    CACHE_FOLDER = 'cache'
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TWELVELABS_API_KEY = os.getenv("TWELVELABS_API_KEY")
    
    APP_URL = os.getenv('APP_URL')
    
    GEMINI_GENERATION_CONFIG = {
        "temperature": 0.4,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    # Public Indexes
    PUBLIC_INDEXES = [
        {
            "id": "public1",
            "name": "Dance (Public)",
            "url": "https://playground.twelvelabs.io/indexes/684367740bc747718ef25e2c", 
            "index_id": "684367740bc747718ef25e2c"
        },
        {
            "id": "public2", 
            "name": "Sports (Public)", 
            "url": "https://playground.twelvelabs.io/indexes/67cad6b2f8affe8f9e7b46d0",
            "index_id": "67cad6b2f8affe8f9e7b46d0"
        }
    ]
    
    @staticmethod
    def create_directories():
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.VIDEO_FOLDER, exist_ok=True)
        os.makedirs(Config.CACHE_FOLDER, exist_ok=True)