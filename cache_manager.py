import os
import base64
import cv2
from datetime import datetime
from config import Config

class CacheManager:
    def __init__(self):
        self.video_frames_cache = {}
    
    def adaptive_frame_quality(self, video_path, target_frames=10):

        try:
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            
            frame_dimensions = (640, 360)
            jpeg_quality = 80
            
            if file_size_mb > 100:
                frame_dimensions = (320, 180)
                jpeg_quality = 60
            elif file_size_mb > 50:
                frame_dimensions = (480, 270)
                jpeg_quality = 70
            elif file_size_mb < 10:
                frame_dimensions = (854, 480)
                jpeg_quality = 90
            
            return {
                "dimensions": frame_dimensions,
                "quality": jpeg_quality,
                "target_frames": target_frames
            }
        except Exception as e:
            print(f"Error determining adaptive quality: {str(e)}")
            return {
                "dimensions": (640, 360),
                "quality": 80,
                "target_frames": target_frames
            }
    # Extract frames from video and cache them
    def extract_and_cache_frames(self, video_path, num_frames=10, cache_key=None):

        if cache_key and cache_key in self.video_frames_cache:
            print(f"Using cached frames for {cache_key}")
            return self.video_frames_cache[cache_key]
        
        print(f"Extracting frames from video: {video_path}")
        frames = []
        try:
            quality_settings = self.adaptive_frame_quality(video_path, num_frames)
            dimensions = quality_settings["dimensions"]
            jpeg_quality = quality_settings["quality"]
            num_frames = quality_settings["target_frames"]
            
            video = cv2.VideoCapture(video_path)
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = video.get(cv2.CAP_PROP_FPS)
            
            if fps <= 0:
                video.release()
                print("Error: Unable to determine video FPS.")
                return []

            frame_interval = total_frames // num_frames
            current_frame = 0
            extracted = 0

            while video.isOpened() and extracted < num_frames:
                ret, frame = video.read()
                if not ret:
                    break
                if current_frame % frame_interval == 0:
                    resized_frame = cv2.resize(frame, dimensions)
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
                    _, buffer = cv2.imencode('.jpg', resized_frame, encode_param)
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    frames.append({
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_base64
                        }
                    })
                    extracted += 1
                current_frame += 1

            video.release()
            
            if cache_key:
                self.video_frames_cache[cache_key] = frames
                print(f"Cached {len(frames)} frames for {cache_key} at quality {jpeg_quality}, dimensions {dimensions}")
                
                # Save to disk cache
                cache_dir = os.path.join(Config.CACHE_FOLDER, cache_key)
                os.makedirs(cache_dir, exist_ok=True)
                
                for i, frame in enumerate(frames):
                    frame_path = os.path.join(cache_dir, f"frame_{i}.jpg")
                    with open(frame_path, "wb") as f:
                        f.write(base64.b64decode(frame["inline_data"]["data"]))
                    
            return frames
        
        except Exception as e:
            print(f"Error extracting frames: {str(e)}")
            return []

    def load_cached_frames_from_disk(self, video_id, model):

        model_suffix = {
            "gemini": "gemini-1.5-pro",
            "gemini-2.5": "gemini-2.5-pro-exp-03-25",
            "gpt4o": "gpt4o"
        }.get(model, "gemini-1.5-pro")
        
        cache_key = f"{video_id}_{model_suffix}"
        
        if cache_key in self.video_frames_cache:
            return {"cached": True, "frames": self.video_frames_cache[cache_key]}
        
        cache_dir = os.path.join(Config.CACHE_FOLDER, cache_key)
        if not os.path.exists(cache_dir) or not os.listdir(cache_dir):
            return {"cached": False, "error": f"No cached frames found for {cache_key}"}
        
        frames = []
        frame_files = sorted([f for f in os.listdir(cache_dir) if f.startswith('frame_')], 
                            key=lambda x: int(x.split('_')[1].split('.')[0]))
        
        for frame_file in frame_files:
            frame_path = os.path.join(cache_dir, frame_file)
            with open(frame_path, 'rb') as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                frames.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img_base64
                    }
                })
        
        if frames:
            self.video_frames_cache[cache_key] = frames
            return {"cached": True, "frames": frames, "loaded_from_disk": True}
        else:
            return {"cached": False, "error": "No frames could be loaded"}

    def clear_cache(self):
        self.video_frames_cache.clear()
        
        cache_dir = Config.CACHE_FOLDER
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            if os.path.isdir(item_path):
                for file in os.listdir(item_path):
                    os.remove(os.path.join(item_path, file))
                os.rmdir(item_path)
            else:
                os.remove(item_path)

    def clean_video_cache(self):

        try:
            print(f"Cleaning video cache at {datetime.now()}")
            cache_size = len(self.video_frames_cache)
            
            if cache_size > 10:
                keys_to_remove = sorted(self.video_frames_cache.keys())[:(cache_size - 10)]
                for key in keys_to_remove:
                    del self.video_frames_cache[key]
                    cache_dir = os.path.join(Config.CACHE_FOLDER, key)
                    if os.path.exists(cache_dir):
                        for file in os.listdir(cache_dir):
                            os.remove(os.path.join(cache_dir, file))
                        os.rmdir(cache_dir)
                print(f"Cache cleaned, removed {len(keys_to_remove)} entries, {len(self.video_frames_cache)} remain")
        except Exception as e:
            print(f"Error cleaning cache: {str(e)}")

    def get_cache_stats(self):

        memory_cache_size = len(self.video_frames_cache)
        memory_cache_keys = list(self.video_frames_cache.keys())
        
        cache_dir = Config.CACHE_FOLDER
        disk_cache_items = []
        total_disk_size = 0
        
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            if os.path.isdir(item_path):
                dir_size = sum(os.path.getsize(os.path.join(item_path, f)) for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)))
                total_disk_size += dir_size
                disk_cache_items.append({
                    "key": item,
                    "size_bytes": dir_size,
                    "size_mb": round(dir_size / (1024 * 1024), 2),
                    "files": len(os.listdir(item_path))
                })
        
        return {
            "memory_cache": {
                "count": memory_cache_size,
                "keys": memory_cache_keys
            },
            "disk_cache": {
                "count": len(disk_cache_items),
                "total_size_mb": round(total_disk_size / (1024 * 1024), 2),
                "items": disk_cache_items
            }
        }