import base64
import boto3
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NovaModel:

    
    def __init__(self):
        self.api_key = None  # Not needed for AWS Bedrock
        self.region = "us-east-1"
        self.model_id = "us.amazon.nova-lite-v1:0"
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):

        try:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.region
            )
            logger.info(f"Bedrock client initialized for region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self.client = None
    
    def analyze_video(self, video_path: str, prompt: str, **kwargs) -> str:

        try:
            if not self.client:
                return "Error: Bedrock client not initialized"
            
            # Read and encode video file
            with open(video_path, "rb") as video_file:
                binary_data = video_file.read()
                base64_string = base64.b64encode(binary_data).decode("utf-8")
            
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
            
            # Invoke model
            response = self.client.invoke_model(
                modelId=self.model_id, 
                body=json.dumps(native_request)
            )
            
            # Parse response
            model_response = json.loads(response["body"].read())
            content_text = model_response["output"]["message"]["content"][0]["text"]
            
            logger.info(f"Nova model analysis completed successfully")
            return content_text
            
        except Exception as e:
            error_msg = f"Error in Nova model analysis: {str(e)}"
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