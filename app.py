from flask import Flask, render_template
import atexit
import requests
import os
from datetime import datetime

from config import Config
from cache_manager import CacheManager
from services.twelvelabs_service import TwelveLabsService
from services.video_service import VideoService
from models.gemini_model import GeminiModel
from models.openai_model import OpenAIModel
from routes.api_routes import create_api_routes

from apscheduler.schedulers.background import BackgroundScheduler

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['VIDEO_FOLDER'] = Config.VIDEO_FOLDER
    app.config['CACHE_FOLDER'] = Config.CACHE_FOLDER

    Config.create_directories()

    # Initialize services
    cache_manager = CacheManager()
    twelvelabs_service = TwelveLabsService()
    video_service = VideoService(cache_manager)
    gemini_model = GeminiModel()
    openai_model = OpenAIModel()


    api_routes = create_api_routes(
        twelvelabs_service, 
        gemini_model, 
        openai_model, 
        video_service, 
        cache_manager
    )
    app.register_blueprint(api_routes, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template('index.html')

    def wake_up_app():
        try:
            app_url = Config.APP_URL
            if app_url:
                response = requests.get(app_url)
                if response.status_code == 200:
                    print(f"Successfully pinged {app_url} at {datetime.now()}")
                else:
                    print(f"Failed to ping {app_url} (status code: {response.status_code}) at {datetime.now()}")
            else:
                print("APP_URL environment variable not set.")
        except Exception as e:
            print(f"Error occurred while pinging app: {e}")

    def clean_cache_task():
        cache_manager.clean_video_cache()

    scheduler = BackgroundScheduler()
    scheduler.add_job(wake_up_app, 'interval', minutes=9)
    scheduler.add_job(clean_cache_task, 'interval', hours=24)
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())

    return app

def main():
    app = create_app()
    
    if __name__ == '__main__':
        app.run(debug=True)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)