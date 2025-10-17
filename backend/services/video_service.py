import os
import yt_dlp
import threading
import time
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
    

    # Select a video for processing using optimized URL-based frame extraction
    def select_video(self, index_id, video_id, twelvelabs_service, is_public=False, actual_index_id=None):

        try:
            target_index_id = actual_index_id if is_public else index_id

            video_url = twelvelabs_service.get_video_url(target_index_id, video_id)
            if not video_url:
                return {
                    "success": False,
                    "error": "Could not get video URL"
                }
            
            # Check if we already have cached frames for this video
            # Use a base cache key that can be extended by models
            cache_key = f"{video_id}_base"
            if self.cache_manager.has_cached_frames(cache_key):
                frame_count = self.cache_manager.get_cached_frames_count(cache_key)
                print(f"✅ Using existing {frame_count} cached frames for video {video_id}")
                return {
                    "success": True,
                    "video_id": video_id,
                    "video_url": video_url,
                    "message": f"Video selected successfully (using {frame_count} cached frames)",
                    "public": is_public,
                    "cached": True,
                    "frame_count": frame_count
                }
            
            # Extract frames directly from URL without downloading the entire video
            print(f"Extracting frames directly from URL for video {video_id}")
            
            # Start frame extraction in background thread
            extraction_thread = threading.Thread(
                target=self.cache_manager.extract_frames_from_url,
                args=(video_url, 10, cache_key)
            )
            extraction_thread.daemon = True
            extraction_thread.start()
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": video_url,
                "message": "Video selected successfully (extracting frames from URL)",
                "public": is_public,
                "cached": False,
                "extraction_in_progress": True
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error selecting video: {str(e)}"
            }
    
    def wait_for_frames(self, video_id, timeout=30):
        """
        Wait for frame extraction to complete for a video
        """
        base_cache_key = f"{video_id}_base"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if base_cache_key in self.cache_manager.video_frames_cache:
                frames = self.cache_manager.video_frames_cache[base_cache_key]
                if frames and len(frames) > 0:
                    print(f"Frames ready for video {video_id}: {len(frames)} frames")
                    return True
            time.sleep(0.5)  # Check every 500ms
        
        print(f"Timeout waiting for frames for video {video_id}")
        return False
    
    def select_video_for_nova(self, index_id, video_id, twelvelabs_service, is_public=False, actual_index_id=None):
        """
        Select and download video specifically for Nova model
        """
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
            
            # Check if video file already exists
            if os.path.exists(output_path):
                print(f"✅ Video file already exists for Nova: {output_path}")
                return {
                    "success": True,
                    "video_id": video_id,
                    "video_path": output_path,
                    "video_url": video_url,
                    "message": "Video selected successfully (using existing video file for Nova)",
                    "public": is_public,
                    "cached": True
                }
            
            # Download video for Nova
            print(f"📥 Downloading video for Nova model: {video_id}")
            if self.download_video(video_url, output_path):
                return {
                    "success": True,
                    "video_id": video_id,
                    "video_path": output_path,
                    "video_url": video_url,
                    "message": "Video selected successfully (downloaded for Nova)",
                    "public": is_public,
                    "cached": False
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to download video for Nova"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error selecting video for Nova: {str(e)}"
            }
    
    def get_video_status(self, video_id, video_path):

        if not video_id or not video_path:
            return {
                "success": False,
                "error": "No video currently selected"
            }
        
        gemini_cache_key = f"{video_id}_gemini-1.5-pro"
        gemini20flash_cache_key = f"{video_id}_gemini-2.0-flash"
        gpt4o_cache_key = f"{video_id}_gpt4o"
        
        cache_status = {
            "video_id": video_id,
            "file_exists": os.path.exists(video_path),
            "file_size_mb": round(os.path.getsize(video_path) / (1024 * 1024), 2) if os.path.exists(video_path) else 0,
            "cached_frames": {
                "gemini": gemini_cache_key in self.cache_manager.video_frames_cache,
                "gemini-2.0-flash": gemini20flash_cache_key in self.cache_manager.video_frames_cache,
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
                args=(video_path, 10, f"{video_id}_gemini-2.0-flash")
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