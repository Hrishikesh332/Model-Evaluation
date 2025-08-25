import os
import base64
import cv2
from openai import OpenAI
from config import Config

class OpenAIModel:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def update_api_key(self, api_key):

        self.api_key = api_key
        self.client = OpenAI(api_key=api_key) if api_key else None
    

    # Generate response using GPT-4o model
    def generate_response(self, prompt, video_path=None, cache_manager=None):

        try:
            if not self.api_key:
                return "OpenAI API key not configured. Please add it to your environment or connect via API settings."
            
            if not self.client:
                return "OpenAI client not initialized."
            
            # Text prompt
            if not video_path or not os.path.exists(video_path):
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant that analyzes videos."},
                    {"role": "user", "content": prompt}
                ]
                
                completion = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=1000
                )
                
                return completion.choices[0].message.content
            
            # Video analysis
            print(f"Processing video for GPT-4o: {video_path}")
            
            video_id = os.path.basename(video_path).split('.')[0]
            cache_key = f"{video_id}_gpt4o"
            
            base64_frames = []

            # Check if frames are cached
            if cache_manager and cache_key in cache_manager.video_frames_cache:
                print(f"Using cached frames for GPT-4o: {cache_key}")
                cached_frames = cache_manager.video_frames_cache[cache_key]
                for frame in cached_frames:
                    base64_frames.append(frame["inline_data"]["data"])
            else:
                # Extract frames from video
                base64_frames = self._extract_frames_for_gpt4o(video_path, cache_manager, cache_key)
            
            if not base64_frames:
                return "Error: Could not extract frames from video."
            
            content = [{"type": "text", "text": prompt}]
            for frame in base64_frames:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{frame}"}
                })
            
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that analyzes videos."},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error in GPT-4o response: {str(e)}")
            return f"Error generating GPT-4o response: {str(e)}"
    


    def _extract_frames_for_gpt4o(self, video_path, cache_manager, cache_key):

        try:
            video = cv2.VideoCapture(video_path)
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_interval = max(total_frames // 10, 1)
            
            base64_frames = []
            extracted_frames = []
            
            for frame_idx in range(0, total_frames, sample_interval):
                video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                success, frame = video.read()
                if not success:
                    continue
                
                frame = cv2.resize(frame, (320, 180))
                _, buffer = cv2.imencode(".jpg", frame)
                encoded_frame = base64.b64encode(buffer).decode("utf-8")
                base64_frames.append(encoded_frame)
                
                extracted_frames.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_frame
                    }
                })
                
                if len(base64_frames) >= 10:
                    break
            
            video.release()
            
            # Cache the frames
            if cache_manager:
                cache_manager.video_frames_cache[cache_key] = extracted_frames
                print(f"Cached {len(extracted_frames)} frames for GPT-4o: {cache_key}")
            
            return base64_frames
            
        except Exception as e:
            print(f"Error extracting frames for GPT-4o: {str(e)}")
            return []
    
    def test_connection(self):
        try:
            if not self.api_key or not self.client:
                return False, "No API key or client not initialized"
            
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"