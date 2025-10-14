import requests
import json
from config import Config

class TwelveLabsService:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.TWELVELABS_API_KEY
        # Remove dependency on old client format - use direct API calls
    
    def update_api_key(self, api_key):
        self.api_key = api_key
    

    # Get all indexes from TwelveLabs
    def get_indexes(self):
       
        if not self.api_key:
            return []
            
        url = "https://api.twelvelabs.io/v1.3/indexes?page=1&page_limit=10&sort_by=created_at&sort_option=desc"
        headers = {
            "accept": "application/json",
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            print(f"API Response Status: {response.status_code}")
            print(f"API Response Body: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    indexes = [
                        {
                            "id": index.get("_id", ""),
                            "name": index.get("index_name", f"Index {i+1}"),
                            "url": f"https://playground.twelvelabs.io/indexes/{index.get('_id', '')}"
                        }
                        for i, index in enumerate(data.get("data", []))
                    ]
                    return indexes
                else:
                    print(f"Unexpected API response structure: {data}")
                    return []
            else:
                print(f"Error fetching indexes: Status {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Exception fetching indexes: {str(e)}")
            return []


    # Get videos from a specific index
    def get_index_videos(self, index_id):

        if not self.api_key:
            return []
            
        url = f"https://api.twelvelabs.io/v1.3/indexes/{index_id}/videos?page=1&page_limit=10&sort_by=created_at&sort_option=desc"
        headers = {
            "accept": "application/json",
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            print(f"Videos API Response Status: {response.status_code}")
            print(f"Videos API Response Body: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    videos = []

                    for idx, video in enumerate(data.get("data", [])):
                        video_id = video.get("_id", "")
                        video_details = self.get_video_details(index_id, video_id)
                        
                        thumbnail_url = None
                        if video_details and "hls" in video_details and "thumbnail_urls" in video_details["hls"]:
                            if video_details["hls"]["thumbnail_urls"]:
                                thumbnail_url = video_details["hls"]["thumbnail_urls"][0]
                        
                        if not thumbnail_url:
                            thumbnail_url = f"/api/thumbnails/{index_id}/{video_id}"
                        
                        videos.append({
                            "id": video_id,
                            "name": video.get("system_metadata", {}).get("filename", f"Video {idx+1}"),
                            "thumbnailUrl": thumbnail_url,
                            "duration": video.get("system_metadata", {}).get("duration", 0)
                        })
                        
                    return videos
                else:
                    print(f"Unexpected videos API response structure: {data}")
                    return []
            else:
                print(f"Error fetching videos: Status {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Exception fetching videos: {str(e)}")
            return []


    # Get details for a specific video
    def get_video_details(self, index_id, video_id):

        if not self.api_key:
            raise Exception("No API key available")
            
        url = f"https://api.twelvelabs.io/v1.3/indexes/{index_id}/videos/{video_id}?embed=false"
        headers = {
            "accept": "application/json",
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get video details: Status {response.status_code}")
                print(f"Response: {response.text}")
                # Raise an exception with the status code for proper error handling
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Exception getting video details: {str(e)}")
            raise e

    def get_video_url(self, index_id, video_id):

        if not self.api_key:
            return None
            
        url = f"https://api.twelvelabs.io/v1.3/indexes/{index_id}/videos/{video_id}"
        headers = {
            "accept": "application/json",
            "x-api-key": self.api_key
        }
        try:
            response = requests.get(url, headers=headers)
            print(f"Video URL API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                video_url = data.get('hls', {}).get('video_url', None)
                if not video_url:
                    print("No HLS URL found in the response. Response data:", data)
                return video_url
            else:
                print(f"Failed to get video URL: Status {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Exception getting video URL: {str(e)}")
            return None

    def get_video_thumbnail(self, index_id, video_id):
        if not self.api_key:
            return None
            
        url = f"https://api.twelvelabs.io/v1.3/indexes/{index_id}/videos/{video_id}/thumbnail"
        headers = {
            "accept": "image/jpeg",
            "x-api-key": self.api_key
        }
        
        try:
            print(f"Requesting thumbnail from: {url}")
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print(f"Thumbnail fetched successfully for video: {video_id}")
                return response.content
            else:
                print(f"Thumbnail fetch failed with status: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception getting thumbnail: {str(e)}")
            return None

    # Generate response using Pegasus model
    def generate_response(self, video_id, prompt, index_id=None):
        try:
            if not self.api_key:
                return "TwelveLabs API key not available. Please check your API key."
                
            print(f"Generating Pegasus response with video_id: {video_id}, prompt: {prompt}")
            
            enhanced_prompt = f"""Analyze the video thoroughly and provide a detailed response to this question: {prompt}

            Please include:
            - Specific details from the video content
            - Timestamps for key moments whenever relevant in mm:ss-mm:ss format
            - Clear explanations of visual elements, performances, and techniques
            - Context that helps understand the significance of what is shown
            
            Focus on providing an informative and comprehensive analysis.
            """
            
            # Use direct API call with current TwelveLabs API format
            headers = {
                "accept": "application/json",
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Current TwelveLabs API endpoint for text generation
            url = "https://api.twelvelabs.io/v1.3/analyze"
            payload = {
                "video_id": video_id,
                "prompt": enhanced_prompt
                # Remove invalid parameters - TwelveLabs API doesn't support max_tokens or temperature
            }
            
            print(f"Making direct API call to TwelveLabs generate endpoint: {url}")
            print(f"Payload: {payload}")
            
            response = requests.post(url, json=payload, headers=headers)
            print(f"API Response Status: {response.status_code}")
            print(f"API Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"Raw response text: {response.text}")
                
                # Handle streaming response format (multiple JSON lines)
                if '\n' in response.text:
                    print("Detected streaming response format")
                    lines = response.text.strip().split('\n')
                    full_text = ""
                    
                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                line_data = json.loads(line)
                                if line_data.get('event_type') == 'text_generation':
                                    text_chunk = line_data.get('text', '')
                                    full_text += text_chunk
                                    print(f"Text chunk: {text_chunk}")
                                elif line_data.get('event_type') == 'stream_end':
                                    print(f"Stream ended: {line_data}")
                            except json.JSONDecodeError:
                                print(f"Failed to parse line: {line}")
                    
                    if full_text:
                        print(f"Full assembled text: {full_text}")
                        return full_text
                    else:
                        return "No text content found in streaming response"
                
                # Handle single JSON response
                try:
                    result = response.json()
                    print(f"API Response Body: {result}")
                    
                    # Handle different response formats
                    if 'text' in result:
                        return result['text']
                    elif 'data' in result and 'text' in result['data']:
                        return result['data']['text']
                    elif 'response' in result and 'text' in result['response']:
                        return result['response']['text']
                    elif 'content' in result:
                        return result['content']
                    else:
                        print(f"Unexpected response format: {result}")
                        return f"Response received but format unexpected: {str(result)[:200]}..."
                        
                except Exception as json_error:
                    print(f"JSON parsing error: {json_error}")
                    print(f"Raw response text: {response.text}")
                    
                    # Try to extract text from raw response
                    raw_text = response.text.strip()
                    if raw_text:
                        # Look for common patterns in the response
                        if '"text":' in raw_text:
                            # Try to extract text field manually
                            try:
                                import re
                                text_match = re.search(r'"text":\s*"([^"]*)"', raw_text)
                                if text_match:
                                    return text_match.group(1)
                            except:
                                pass
                        
                        # Return first 500 characters of raw response as fallback
                        return f"Raw response (first 500 chars): {raw_text[:500]}"
                    else:
                        return "Empty response received from API"
            else:
                print(f"TwelveLabs API Error: {response.status_code}")
                print(f"Error Response: {response.text}")
                return f"API Error {response.status_code}: {response.text}"
                    
        except Exception as e:
            print(f"Exception generating Pegasus response: {str(e)}")
            return f"An error occurred while generating a response: {str(e)}"