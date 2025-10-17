import base64
import boto3
import json
import logging
import os
import cv2
import tempfile
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class NovaModel:

    
    def __init__(self):
        self.api_key = None  # Not needed for AWS Bedrock
        self.region = Config.AWS_DEFAULT_REGION
        self.model_id = "amazon.nova-lite-v1:0"
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS Bedrock client with credentials"""
        try:
            # Try multiple authentication methods
            auth_methods = [
                {
                    'name': 'Explicit credentials',
                    'client': lambda: boto3.client(
                        "bedrock-runtime",
                        region_name=self.region,
                        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
                    )
                },
                {
                    'name': 'Session with credentials',
                    'client': lambda: boto3.Session(
                        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                        region_name=self.region
                    ).client("bedrock-runtime")
                },
                {
                    'name': 'Default credentials',
                    'client': lambda: boto3.client(
                        "bedrock-runtime",
                        region_name=self.region
                    )
                }
            ]
            
            for method in auth_methods:
                try:
                    logger.info(f"Trying authentication method: {method['name']}")
                    self.client = method['client']()
                    
                    # Test the client with a simple call (bedrock-runtime doesn't have list_foundation_models)
                    # Just check if client is created successfully
                    logger.info(f"✅ Bedrock client initialized successfully with {method['name']} for region: {self.region}")
                    return
                    
                except Exception as e:
                    logger.warning(f"❌ {method['name']} failed: {e}")
                    continue
            
            # If all methods failed
            logger.error("All authentication methods failed")
            self.client = None
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self.client = None
    
    def _preprocess_video(self, video_path: str, max_frames: int = 5, max_size_mb: int = 10) -> str:
        """
        Preprocess video to extract key frames and reduce size for Nova model
        """
        try:
            # Check original file size
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            logger.info(f"Original video size: {file_size_mb:.2f} MB")
            
            if file_size_mb <= max_size_mb:
                # File is small enough, use original
                logger.info("Video size is acceptable, using original")
                return video_path
            
            # Extract key frames
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"Video info: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s duration")
            
            # Check if video is too long (Nova has duration limits)
            if duration > 60:  # Limit to 60 seconds
                logger.warning(f"Video too long ({duration:.1f}s), limiting to first 60 seconds")
                # Calculate frames for first 60 seconds
                max_frames_for_duration = int(60 * fps)
                total_frames = min(total_frames, max_frames_for_duration)
            
            # Calculate frame interval
            frame_interval = max(1, total_frames // max_frames)
            
            # Create temporary video with key frames
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_path = temp_video.name
            temp_video.close()
            
            # Get video properties and reduce resolution for smaller file size
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Reduce resolution to max 480p for smaller file size
            max_width = 640
            max_height = 480
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
            else:
                new_width = width
                new_height = height
            
            # Reduce frame rate to 10 fps for smaller file size
            new_fps = min(fps, 10.0)
            
            logger.info(f"Reducing video from {width}x{height}@{fps:.1f}fps to {new_width}x{new_height}@{new_fps:.1f}fps")
            
            # Create video writer with reduced settings
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_path, fourcc, new_fps, (new_width, new_height))
            
            frame_count = 0
            frames_written = 0
            
            while frames_written < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    # Resize frame if needed
                    if new_width != width or new_height != height:
                        frame = cv2.resize(frame, (new_width, new_height))
                    out.write(frame)
                    frames_written += 1
                
                frame_count += 1
            
            cap.release()
            out.release()
            
            # Check new file size
            new_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            logger.info(f"Preprocessed video size: {new_size_mb:.2f} MB ({frames_written} frames)")
            
            if new_size_mb > max_size_mb:
                # Still too large, try with fewer frames
                logger.warning(f"Preprocessed video still too large ({new_size_mb:.2f} MB), trying with fewer frames")
                os.unlink(temp_path)
                return self._preprocess_video(video_path, max_frames // 2, max_size_mb)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Error preprocessing video: {e}")
            # Fallback to original video
            return video_path
    
    def _fallback_analysis(self, video_path: str, prompt: str) -> str:
        """
        Fallback analysis when video is too large for Nova
        """
        try:
            # Extract a few key frames and analyze them
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return "Error: Could not open video file for fallback analysis"
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            # Extract 3 key frames
            frame_indices = [0, total_frames // 2, total_frames - 1]
            frames_info = []
            
            for i, frame_idx in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    timestamp = frame_idx / fps if fps > 0 else 0
                    frames_info.append(f"Frame {i+1} at {timestamp:.1f}s")
            
            cap.release()
            
            # Create a text-based analysis
            analysis = f"""Video Analysis (Fallback Mode):
            
Video Information:
- Duration: {duration:.1f} seconds
- Total frames: {total_frames}
- FPS: {fps:.1f}
- Key frames analyzed: {len(frames_info)}

Note: This video was too large for direct analysis by AWS Nova. 
The analysis is based on video metadata and key frame extraction.

Prompt: {prompt}

Analysis: Based on the video structure, this appears to be a {duration:.1f}-second video with {total_frames} frames. 
For a more detailed analysis, please try with a shorter video or contact support for assistance with large file processing."""
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in fallback analysis: {e}")
            return f"Error: Could not analyze video - {str(e)}"
    
    def analyze_video(self, video_path: str, prompt: str, **kwargs) -> str:

        try:
            if not self.client:
                return "Error: Bedrock client not initialized"
            
            # Try multiple model IDs and approaches
            model_ids_to_try = [
                "amazon.nova-lite-v1:0",
                "amazon.nova-micro-v1:0", 
                "amazon.nova-pro-v1:0"
            ]
            
            for model_id in model_ids_to_try:
                try:
                    logger.info(f"Trying model ID: {model_id}")
                    result = self._try_analyze_with_model(video_path, prompt, model_id, **kwargs)
                    if result and not result.startswith("Error:"):
                        logger.info(f"✅ Success with model: {model_id}")
                        return result
                    else:
                        logger.warning(f"❌ Failed with model: {model_id}")
                        continue
                except Exception as e:
                    error_msg = f"Error in Nova model analysis with {model_id}: {str(e)}"
                    logger.warning(f"❌ {error_msg}")
                    # Return the error message instead of continuing
                    return error_msg
            
            # If all models failed, return fallback
            logger.warning("All Nova models failed, using fallback analysis")
            return self._fallback_analysis(video_path, prompt)
            
        except Exception as e:
            error_msg = f"Error in Nova model analysis: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _try_analyze_with_model(self, video_path: str, prompt: str, model_id: str, **kwargs) -> str:
        """Try to analyze video with a specific model ID"""
        try:
            # Preprocess video to reduce size
            processed_video_path = self._preprocess_video(video_path)
            temp_file_created = processed_video_path != video_path
            
            try:
                # Read and encode video file
                with open(processed_video_path, "rb") as video_file:
                    binary_data = video_file.read()
                    base64_string = base64.b64encode(binary_data).decode("utf-8")
                
                # Check if the encoded data is still too large (AWS has limits)
                data_size_mb = len(base64_string) / (1024 * 1024)
                logger.info(f"Base64 encoded data size: {data_size_mb:.2f} MB")
                
                if data_size_mb > 10:  # AWS Nova has strict input size limits
                    logger.warning(f"Data still too large ({data_size_mb:.2f} MB), using fallback analysis")
                    return self._fallback_analysis(video_path, prompt)
                
                logger.info(f"✅ Data size acceptable ({data_size_mb:.2f} MB), proceeding with Nova analysis")
                
                # Define system prompt
                system_list = [
                    {
                        "text": "You are an expert media analyst. When the user provides you with a video, provide a detailed analysis based on the user's question."
                    }
                ]
                
                # Define user message
                message_list = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "video": {
                                    "format": "mp4",
                                    "source": {
                                        "bytes": base64_string
                                    },
                                }
                            },
                            {
                                "text": prompt
                            },
                        ],
                    }
                ]
                
                # Configure inference parameters
                inf_params = {
                    "maxTokens": kwargs.get("max_tokens", 500),
                    "topP": kwargs.get("top_p", 0.9),
                    "topK": kwargs.get("top_k", 50),
                    "temperature": kwargs.get("temperature", 0.7)
                }
                
                # Create request
                native_request = {
                    "schemaVersion": "messages-v1",
                    "messages": message_list,
                    "system": system_list,
                    "inferenceConfig": inf_params,
                }
                
                # Invoke model with the specific model_id
                response = self.client.invoke_model(
                    modelId=model_id, 
                    body=json.dumps(native_request)
                )
                
                # Parse response
                response_body = response["body"].read()
                logger.info(f"Raw response from Nova API: {response_body[:200]}...")
                
                model_response = json.loads(response_body)
                logger.info(f"Parsed response structure: {list(model_response.keys())}")
                
                if "output" in model_response and "message" in model_response["output"]:
                    content_text = model_response["output"]["message"]["content"][0]["text"]
                    logger.info(f"Nova model analysis completed successfully with {model_id}")
                    logger.info(f"Response text length: {len(content_text)} characters")
                    return content_text
                else:
                    logger.error(f"Unexpected response structure: {model_response}")
                    return f"Error: Unexpected response structure from Nova model"
                
            finally:
                # Clean up temporary file if created
                if temp_file_created and os.path.exists(processed_video_path):
                    try:
                        os.unlink(processed_video_path)
                        logger.info("Cleaned up temporary video file")
                    except Exception as e:
                        logger.warning(f"Could not clean up temporary file: {e}")
            
        except Exception as e:
            error_msg = f"Error in Nova model analysis with {model_id}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def is_available(self) -> bool:
        """Check if the model is available"""
        return self.client is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "name": "nova",
            "display_name": "AWS Bedrock Nova",
            "provider": "Amazon",
            "model_id": self.model_id,
            "region": self.region,
            "available": self.is_available(),
            "capabilities": ["video_analysis", "multimodal"]
        } 