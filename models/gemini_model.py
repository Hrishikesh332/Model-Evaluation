import os
import base64
import google.generativeai as genai
from config import Config

class GeminiModel:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    def update_api_key(self, api_key):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
    

    # Generate response using Gemini model
    def generate_response(self, prompt, video_path=None, model_name="gemini-1.5-pro", cache_manager=None):
        
        try:
            if not self.api_key:
                return "Gemini API key not configured. Please add it to your environment or connect via API settings."

            model = genai.GenerativeModel(model_name=model_name)

            # Text prompt
            if not video_path or not os.path.exists(video_path):
                response = model.generate_content(prompt)
                try:
                    return response.candidates[0].content.parts[0].text
                except (AttributeError, IndexError):
                    return f"Error extracting response text. Raw response: {str(response)}"

            # Video analysis
            video_id = os.path.basename(video_path).split('.')[0]
            cache_key = f"{video_id}_{model_name}"

            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)

            if file_size_mb > 8:
                # Use frame extraction for large videos
                if cache_manager:
                    frames = cache_manager.extract_and_cache_frames(video_path, num_frames=10, cache_key=cache_key)
                else:
                    return "Cache manager not available for frame extraction."
                
                if not frames:
                    return "Error: Could not extract frames from the video."

                multimodal_content = [{"text": f"Analyze the video frames to answer: {prompt}"}]
                multimodal_content.extend(frames)
                multimodal_content.append({"text": f"Based on these video frames, please answer: {prompt}"})

                try:
                    response = model.generate_content(multimodal_content)
                    return "Note: The video was too large. Analysis is based on key frames.\n\n" + response.candidates[0].content.parts[0].text
                except Exception as api_error:
                    return f"Error processing video frames with Gemini: {str(api_error)}"
            else:
                # Direct video processing for smaller files
                with open(video_path, "rb") as f:
                    video_data = f.read()

                multimodal_parts = [
                    {
                        "inline_data": {
                            "mime_type": "video/mp4",
                            "data": base64.b64encode(video_data).decode('utf-8')
                        }
                    },
                    {
                        "text": f"Analyze this video and answer: {prompt}"
                    }
                ]

                try:
                    response = model.generate_content(multimodal_parts)
                    return response.candidates[0].content.parts[0].text
                except Exception as video_error:
                    return f"Error processing video with Gemini: {str(video_error)}"

        except Exception as e:
            return f"Gemini API Error: {str(e)}"
    
    def test_connection(self):
        try:
            if not self.api_key:
                return False, "No API key provided"
            
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content("Hello")
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"