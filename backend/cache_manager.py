import os
import base64
import time
import cv2
import requests
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
        start_time = time.time()
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

            # Calculate truly equidistant frame positions across the entire video
            if total_frames <= num_frames:
                # If video has fewer frames than requested, extract all frames
                frame_positions = list(range(total_frames))
            else:
                # Calculate equidistant positions across the entire video duration
                frame_positions = []
                for i in range(num_frames):
                    # Distribute frames evenly from start to end (inclusive)
                    position = int((i * (total_frames - 1)) / (num_frames - 1))
                    frame_positions.append(position)
            
            print(f"Frame positions: {frame_positions}")
            
            current_frame = 0
            extracted = 0
            position_index = 0

            while video.isOpened() and extracted < num_frames and position_index < len(frame_positions):
                ret, frame = video.read()
                if not ret:
                    break
                
                # Check if current frame is one we want to extract
                if current_frame == frame_positions[position_index]:
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
                    position_index += 1
                    print(f"Extracted frame {extracted}/{num_frames} at position {current_frame}")
                    
                current_frame += 1

            video.release()
            
            extraction_time = time.time() - start_time
            print(f"Frame extraction completed in {extraction_time:.2f}s for {cache_key}")
            
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

    # Extract frames directly from video URL with optimized seeking
    def extract_frames_from_url(self, video_url, num_frames=10, cache_key=None):
        """
        Extract frames directly from video URL using optimized frame seeking.
        This approach is much faster for deployment environments.
        """
        if cache_key and cache_key in self.video_frames_cache:
            cached_frames = self.video_frames_cache[cache_key]
            if cached_frames and len(cached_frames) > 0:
                print(f"✅ Using {len(cached_frames)} cached frames for {cache_key}")
                return cached_frames
            else:
                print(f"⚠️  Cache key {cache_key} exists but has no frames, re-extracting...")
        
        print(f"🔄 Extracting {num_frames} frames from URL: {video_url[:50]}...")
        frames = []
        start_time = time.time()
        
        try:
            # OpenCV can read from URLs directly
            video = cv2.VideoCapture(video_url)
            
            if not video.isOpened():
                print(f"❌ Error: Could not open video URL: {video_url}")
                return []
            
            # Get video properties
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = video.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            if fps <= 0 or total_frames <= 0:
                print("❌ Error: Unable to determine video properties from URL")
                video.release()
                return []
            
            print(f"📹 Video properties: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s duration")
            
            # Optimize for deployment: use configurable quality and dimensions
            frame_dims = Config.FRAME_DIMENSIONS.split('x')
            dimensions = (int(frame_dims[0]), int(frame_dims[1]))
            jpeg_quality = Config.FRAME_QUALITY
            
            # Further optimize for deployment mode
            if Config.DEPLOYMENT_MODE == "production":
                # Reduce frames for faster processing in production
                num_frames = min(num_frames, Config.MAX_FRAMES_PER_VIDEO)
                print(f"🏭 Production mode: limiting to {num_frames} frames")
            
            # Calculate frame positions with optimized distribution
            if total_frames <= num_frames:
                frame_positions = list(range(total_frames))
            else:
                # Use time-based sampling for better distribution
                frame_positions = []
                for i in range(num_frames):
                    # Distribute frames evenly across time
                    time_position = (i * duration) / (num_frames - 1) if num_frames > 1 else 0
                    frame_position = int(time_position * fps)
                    frame_position = min(frame_position, total_frames - 1)
                    frame_positions.append(frame_position)
            
            print(f"🎯 Extracting frames at positions: {frame_positions}")
            
            # Extract frames using direct seeking (much faster)
            for i, frame_pos in enumerate(frame_positions):
                try:
                    # Seek to specific frame position
                    video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                    ret, frame = video.read()
                    
                    if ret and frame is not None:
                        # Resize and encode frame
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
                        print(f"✅ Extracted frame {i+1}/{num_frames} at position {frame_pos}")
                    else:
                        print(f"⚠️ Failed to extract frame at position {frame_pos}")
                        
                except Exception as e:
                    print(f"❌ Error extracting frame at position {frame_pos}: {str(e)}")
                    continue
            
            video.release()
            
            extraction_time = time.time() - start_time
            print(f"⏱️ Frame extraction completed in {extraction_time:.2f}s")
            
            if cache_key and frames:
                self.video_frames_cache[cache_key] = frames
                print(f"💾 Cached {len(frames)} frames for {cache_key}")
                
                # Save to disk cache for future use
                cache_dir = os.path.join(Config.CACHE_FOLDER, cache_key)
                os.makedirs(cache_dir, exist_ok=True)
                
                for i, frame in enumerate(frames):
                    frame_path = os.path.join(cache_dir, f"frame_{i}.jpg")
                    with open(frame_path, "wb") as f:
                        f.write(base64.b64decode(frame["inline_data"]["data"]))
            
            print(f"🎉 Successfully extracted {len(frames)} frames from URL")
            return frames
            
        except Exception as e:
            print(f"Error extracting frames from URL: {str(e)}")
            return []

    def has_cached_frames(self, cache_key):
        """
        Check if frames are already cached for a given cache key
        """
        if cache_key in self.video_frames_cache:
            cached_frames = self.video_frames_cache[cache_key]
            return cached_frames and len(cached_frames) > 0
        return False

    def get_cached_frames_count(self, cache_key):
        """
        Get the number of cached frames for a given cache key
        """
        if cache_key in self.video_frames_cache:
            cached_frames = self.video_frames_cache[cache_key]
            return len(cached_frames) if cached_frames else 0
        return 0

    def load_cached_frames_from_disk(self, video_id, model):

        model_suffix = {
            "gemini": "gemini-1.5-pro",
            "gemini-2.0-flash": "gemini-2.0-flash",
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