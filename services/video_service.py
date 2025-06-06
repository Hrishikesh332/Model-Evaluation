import os
import yt_dlp
import threading
from config import Config

class VideoService:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
    

    def download_video(self, url, output_filename):

        ydl_opts = {
            'format': 'best',
            'outtmpl': output_filename,
            'quiet': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            print(f"Failed to download video: {str(e)}")
            return False
    

    # Select and download a video for processing
    def select_video(self, index_id, video_id, twelvelabs_service, is_public=False, actual_index_id=None):

        try:

            target_index_id = actual_index_id if is_public else index_id

            video_url = twelvelabs_service.get_video_url(target_index_id, video_id)
            if not video_url:
                return {
                    "success": False,
                    "error": "Could not get video URL"
                }
            
            video_filename = f"{video_id}.mp4"
            output_path = os.path.join(Config.VIDEO_FOLDER, video_filename)
            
            # Download video
            if self.download_video(video_url, output_path):
                threading.Thread(
                    target=self.cache_manager.extract_and_cache_frames,
                    args=(output_path, 10, video_id)
                ).start()
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "video_path": output_path,
                    "message": "Video selected and downloaded successfully",
                    "public": is_public
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to download video"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error selecting video: {str(e)}"
            }
    
    def get_video_status(self, video_id, video_path):

        if not video_id or not video_path:
            return {
                "success": False,
                "error": "No video currently selected"
            }
        
        gemini_cache_key = f"{video_id}_gemini-1.5-pro"
        gemini25_cache_key = f"{video_id}_gemini-2.5-pro-exp-03-25"
        gpt4o_cache_key = f"{video_id}_gpt4o"
        
        cache_status = {
            "video_id": video_id,
            "file_exists": os.path.exists(video_path),
            "file_size_mb": round(os.path.getsize(video_path) / (1024 * 1024), 2) if os.path.exists(video_path) else 0,
            "cached_frames": {
                "gemini": gemini_cache_key in self.cache_manager.video_frames_cache,
                "gemini-2.5": gemini25_cache_key in self.cache_manager.video_frames_cache,
                "gpt4o": gpt4o_cache_key in self.cache_manager.video_frames_cache
            }
        }
        
        return {
            "success": True,
            "video_status": cache_status
        }
    
    def preload_frames(self, video_id, video_path):

        if not video_id or not video_path or not os.path.exists(video_path):
            return {
                "success": False,
                "error": "No valid video currently selected"
            }
        
        try:

            threading.Thread(
                target=self.cache_manager.extract_and_cache_frames,
                args=(video_path, 10, f"{video_id}_gemini-1.5-pro")
            ).start()
            
            threading.Thread(
                target=self.cache_manager.extract_and_cache_frames,
                args=(video_path, 10, f"{video_id}_gemini-2.5-pro-exp-03-25")
            ).start()
            
            threading.Thread(
                target=self.cache_manager.extract_and_cache_frames,
                args=(video_path, 10, f"{video_id}_gpt4o")
            ).start()
            
            return {
                "success": True,
                "message": "Frame extraction started for all models"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error starting frame extraction: {str(e)}"
            }