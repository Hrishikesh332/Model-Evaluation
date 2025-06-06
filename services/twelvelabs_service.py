import requests
from twelvelabs import TwelveLabs
from config import Config

class TwelveLabsService:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.TWELVELABS_API_KEY
        self.client = TwelveLabs(api_key=self.api_key) if self.api_key else None
    
    def update_api_key(self, api_key):

        self.api_key = api_key
        self.client = TwelveLabs(api_key=api_key) if api_key else None
    

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
            return None
            
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
                return None
        except Exception as e:
            print(f"Exception getting video details: {str(e)}")
            return None

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
            if not self.client:
                return "TwelveLabs client not initialized. Please check your API key."
                
            print(f"Generating Pegasus response with video_id: {video_id}, prompt: {prompt}")
            
            enhanced_prompt = f"""Analyze the video thoroughly and provide a detailed response to this question: {prompt}

            Please include:
            - Specific details from the video content
            - Timestamps for key moments whenever relevant in mm:ss-mm:ss format
            - Clear explanations of visual elements, performances, and techniques
            - Context that helps understand the significance of what is shown
            
            Focus on providing an informative and comprehensive analysis.
            """
            
            try:
                text_stream = self.client.generate.text_stream(
                    video_id=video_id,
                    prompt=enhanced_prompt
                )
                
                response_text = ""
                for text in text_stream:
                    response_text = text_stream.aggregated_text
                
                return response_text
                
            except AttributeError:
                headers = {
                    "accept": "application/json",
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json"
                }
                url = "https://api.twelvelabs.io/v1.3/generate"
                payload = {
                    "video_id": video_id,
                    "prompt": enhanced_prompt
                }
                
                print("Making direct API call to TwelveLabs generate endpoint")
                response = requests.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'text' in result:
                        return result['text']
                    else:
                        return "The API response didn't contain the expected text content."
                else:
                    print(f"TwelveLabs API Error: {response.status_code} - {response.text}")
                    return f"API Error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            print(f"Exception generating Pegasus response: {str(e)}")
            return f"An error occurred while generating a response: {str(e)}"