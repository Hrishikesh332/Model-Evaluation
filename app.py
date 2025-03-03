from flask import Flask, render_template, request, jsonify, session
import os
import requests
import json
import tempfile
import uuid
import time
import yt_dlp
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
from twelvelabs import TwelveLabs

from google.generativeai import types as genai_types
import time
import base64

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['VIDEO_FOLDER'] = 'videos'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWELVELABS_API_KEY = os.getenv("TWELVELABS_API_KEY")

twelvelabs_client = None
if TWELVELABS_API_KEY:
    twelvelabs_client = TwelveLabs(api_key=TWELVELABS_API_KEY)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    generation_config = {
        "temperature": 0.4,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

PUBLIC_INDEXES = [
    {
        "id": "public1",
        "name": "Hybe_New (Public)",
        "url": "https://playground.twelvelabs.io/indexes/67900e1181c61d781369699f"
    },
    {
        "id": "public2", 
        "name": "Talent Show (Public)", 
        "url": "https://playground.twelvelabs.io/indexes/12345"
    }
]

PUBLIC_VIDEOS = {
    "public1": [
        {"id": "video1", "name": "BTS Performance", "thumbnailUrl": "/static/img/sample1.jpg"},
        {"id": "video2", "name": "SEVENTEEN Dance", "thumbnailUrl": "/static/img/sample2.jpg"}
    ],
    "public2": [
        {"id": "video3", "name": "Singer Audition", "thumbnailUrl": "/static/img/sample3.jpg"},
        {"id": "video4", "name": "Dance Competition", "thumbnailUrl": "/static/img/sample4.jpg"}
    ]
}

def get_twelvelabs_client():

    global twelvelabs_client
    api_key = session.get('twelvelabs_api_key', TWELVELABS_API_KEY)
    
    if api_key and (twelvelabs_client is None or twelvelabs_client.api_key != api_key):
        twelvelabs_client = TwelveLabs(api_key=api_key)
    
    return twelvelabs_client

def get_twelvelabs_indexes(api_key):
    url = "https://api.twelvelabs.io/v1.3/indexes?page=1&page_limit=10&sort_by=created_at&sort_option=desc"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
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

def get_index_videos(index_id, api_key):
    url = f"https://api.twelvelabs.io/v1.3/indexes/{index_id}/videos?page=1&page_limit=10&sort_by=created_at&sort_option=desc"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        print(f"Videos API Response Status: {response.status_code}")
        print(f"Videos API Response Body: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and isinstance(data["data"], list):
                videos = [
                    {
                        "id": video.get("_id", ""),
                        "name": video.get("system_metadata", {}).get("filename", f"Video {idx+1}"),
                        "thumbnailUrl": f"/api/thumbnails/{index_id}/{video.get('_id', '')}",
                        "duration": video.get("system_metadata", {}).get("duration", 0)
                    }
                    for idx, video in enumerate(data.get("data", []))
                ]
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

def get_video_url(index_id, video_id, api_key):
    url = f"https://api.twelvelabs.io/v1.3/indexes/{index_id}/videos/{video_id}"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key
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

@app.route('/api/thumbnails/<index_id>/<video_id>')
def get_video_thumbnail(index_id, video_id):
    api_key = session.get('twelvelabs_api_key', TWELVELABS_API_KEY)
    
    if not api_key:
        return "No API key", 401
    
    url = f"https://api.twelvelabs.io/v1.3/indexes/{index_id}/videos/{video_id}/thumbnail"
    headers = {
        "accept": "image/jpeg",
        "x-api-key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.content, 200, {'Content-Type': 'image/jpeg'}
        else:
            # Return a default thumbnail image
            return app.send_static_file('img/default-thumbnail.jpg')
    except Exception as e:
        print(f"Exception getting thumbnail: {str(e)}")
        return app.send_static_file('img/default-thumbnail.jpg')

def download_video(url, output_filename):

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


def generate_pegasus_response(index_id, video_id, prompt, api_key):
    try:
        client = get_twelvelabs_client()
        if not client:
            return "TwelveLabs client not initialized. Please check your API key."
            
        print(f"Generating Pegasus response with video_id: {video_id}, prompt: {prompt}")
        
        enhanced_prompt = f"""Analyze the video thoroughly and provide a detailed response to this question: {prompt}
        
        Please include -
        - Specific details from the video content
        - Timestamps for key moments whenever relevant in mm:ss-mm:Ss
        - Clear explanations of visual elements, performances, and techniques
        - Context that helps understand the significance of what is shown
        
        Focus on providing an informative and comprehensive analysis.
        """
        
        try:
            text_stream = client.generate.text_stream(
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
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            url = "https://api.twelvelabs.io/v1.3/generate"
            payload = {
                "video_id": video_id,
                "prompt": enhanced_prompt
            }
            
            print(f"Making direct API call to TwelveLabs generate endpoint")
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
                
        except Exception as inner_e:
            print(f"Error in primary Pegasus API call: {str(inner_e)}")
            
            try:
                headers = {
                    "accept": "application/json",
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                }
                url = "https://api.twelvelabs.io/v1.3/generate"
                payload = {
                    "video_id": video_id,
                    "prompt": enhanced_prompt
                }
                
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    return result.get('text', f"Unexpected response format: {result}")
                else:
                    return f"API Error: {response.status_code} - {response.text}"
            except Exception as fallback_error:
                return f"All API methods failed. Error: {str(fallback_error)}"
            
    except Exception as e:
        print(f"Exception generating Pegasus response: {str(e)}")
        return f"An error occurred while generating a response: {str(e)}"



def generate_gemini_response(prompt, video_path=None):

    try:
        api_key = session.get('gemini_api_key', GEMINI_API_KEY)
        if not api_key:
            return "Gemini API key not configured. Please add it to your environment or connect via API settings."
        
        genai.configure(api_key=api_key)
        
        if not video_path or not os.path.exists(video_path):
            model = genai.GenerativeModel(model_name="gemini-1.5-pro")
            response = model.generate_content(prompt)
            return response.text
        
        print(f"Processing video for Gemini analysis: {video_path}")
        
        try:
            with open(video_path, "rb") as f:
                video_data = f.read()
            
            model = genai.GenerativeModel(model_name="gemini-1.5-pro")
            
            multimodal_parts = [
                {
                    "inline_data": {
                        "mime_type": "video/mp4",
                        "data": base64.b64encode(video_data).decode('utf-8')
                    }
                },
                {
                    "text": f"Analyze this video and answer the following question: {prompt}"
                }
            ]
            
            response = model.generate_content(multimodal_parts)
            
            return response.text
            
        except Exception as video_error:
            print(f"Error processing video with Gemini API: {str(video_error)}")
            
            model = genai.GenerativeModel(model_name="gemini-1.5-pro")
            response = model.generate_content(
                f"I was supposed to analyze a video and answer: {prompt}. However, I couldn't process the video. I can only provide a general response based on the question."
            )
            return f"Note: Video processing failed. Providing a general response instead.\n\n{response.text}"
            
    except Exception as e:
        print(f"Error generating Gemini response: {str(e)}")
        return f"An error occurred while generating a response: {str(e)}"


def generate_gpt4o_response(prompt, video_path=None):

    try:
        api_key = session.get('openai_api_key', OPENAI_API_KEY)
        if not api_key:
            return "OpenAI API key not configured. Please add it to your environment or connect via API settings."
        
        client = OpenAI(api_key=api_key)
        
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant that analyzes videos and provides insightful responses."}
        ]
        
        if video_path and os.path.exists(video_path):
            messages.append({
                "role": "user", 
                "content": f"[Video Analysis Request] The following query is about a video that likely contains performances, music videos, or dance routines. Please provide a detailed analysis: {prompt}"
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "text"},
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating GPT-4o response: {str(e)}")
        return f"An error occurred while generating a response: {str(e)}"


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/connect', methods=['POST'])
def connect_api():

    print("Connect API called")
    global twelvelabs_client
    
    api_type = request.json.get('type', 'twelvelabs')
    api_key = request.json.get('api_key')
    
    if not api_key or len(api_key) == 0:
        return jsonify({"status": "error", "message": "Invalid API key"}), 400
    
    print(f"Connecting TwelveLabs API with key: {api_key[:5]}...")
    
    if api_type == 'twelvelabs':
        session['twelvelabs_api_key'] = api_key
        twelvelabs_client = TwelveLabs(api_key=api_key)
        try:
            indexes = get_twelvelabs_indexes(api_key)
            if indexes and len(indexes) > 0:
                session['twelvelabs_indexes'] = indexes
                return jsonify({"status": "success", "message": "TwelveLabs API key connected successfully", "indexes": indexes})
            else:
                return jsonify({"status": "error", "message": "Connected but no indexes found"}), 404
        except Exception as e:
            print(f"Exception in connect_api: {str(e)}")
            return jsonify({"status": "error", "message": f"Failed to connect: {str(e)}"}), 400
    
    elif api_type == 'gemini':
        session['gemini_api_key'] = api_key
        try:
            genai.configure(api_key=api_key)
            genai.GenerativeModel("gemini-1.5-pro").generate_content("Hello")
            return jsonify({"status": "success", "message": "Gemini API key connected successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to connect: {str(e)}"}), 400
    
    elif api_type == 'openai':
        session['openai_api_key'] = api_key
        try:
            client = OpenAI(api_key=api_key)
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}]
            )
            return jsonify({"status": "success", "message": "OpenAI API key connected successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to connect: {str(e)}"}), 400
    
    else:
        return jsonify({"status": "error", "message": "Invalid API type"}), 400

@app.route('/api/indexes', methods=['GET'])
def get_indexes():
    api_key = session.get('twelvelabs_api_key')
    
    if api_key:
        indexes = get_twelvelabs_indexes(api_key)
        if indexes and len(indexes) > 0:
            session['twelvelabs_indexes'] = indexes
            return jsonify({"status": "success", "indexes": indexes})
        else:
            return jsonify({"status": "error", "message": "No indexes found"}), 404
    else:
        return jsonify({"status": "success", "indexes": PUBLIC_INDEXES, "public": True})

@app.route('/api/indexes/<index_id>/videos', methods=['GET'])
def get_videos(index_id):
    api_key = session.get('twelvelabs_api_key')
    
    if api_key:
        videos = get_index_videos(index_id, api_key)
        if videos and len(videos) > 0:
            return jsonify({"status": "success", "videos": videos})
        else:
            return jsonify({"status": "error", "message": "No videos found in this index"}), 404
    else:
        if index_id in PUBLIC_VIDEOS:
            return jsonify({"status": "success", "videos": PUBLIC_VIDEOS[index_id], "public": True})
        else:
            return jsonify({"status": "error", "message": "Invalid index ID"}), 404

@app.route('/api/video/select', methods=['POST'])
def select_video():
    index_id = request.json.get('index_id')
    video_id = request.json.get('video_id')
    
    if not index_id or not video_id:
        return jsonify({"status": "error", "message": "Index ID and Video ID are required"}), 400
    
    session['selected_index_id'] = index_id
    session['selected_video_id'] = video_id
 
    if index_id.startswith('public'):
        return jsonify({
            "status": "success", 
            "message": "Public video selected",
            "video_id": video_id
        })
    
    api_key = session.get('twelvelabs_api_key')
    if not api_key:
        return jsonify({"status": "error", "message": "TwelveLabs API key not found"}), 401
    
    video_url = get_video_url(index_id, video_id, api_key)
    if not video_url:
        return jsonify({"status": "error", "message": "Could not get video URL"}), 404
    
    video_filename = f"{video_id}.mp4"
    output_path = os.path.join(app.config['VIDEO_FOLDER'], video_filename)
    session['video_path'] = output_path
    
    if download_video(video_url, output_path):
        return jsonify({
            "status": "success", 
            "message": "Video selected and downloaded successfully",
            "video_id": video_id,
            "video_path": output_path
        })
    else:
        return jsonify({"status": "error", "message": "Failed to download video"}), 500

@app.route('/api/search', methods=['POST'])
def search_videos():
    """Analyze selected video with query"""
    print("Search endpoint called")
    query = request.json.get('query')
    selected_model = request.json.get('model', 'gemini')
    
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400
    
    index_id = session.get('selected_index_id')
    video_id = session.get('selected_video_id')
    video_path = session.get('video_path')
    
    print(f"Processing query: '{query}' for video_id: {video_id} with model: {selected_model}")
    
    if not index_id or not video_id:
        return jsonify({"status": "error", "message": "No video selected. Please select a video first."}), 400
    
    responses = {}
    
    api_key = session.get('twelvelabs_api_key', TWELVELABS_API_KEY)
    try:
        if api_key:
            pegasus_response = generate_pegasus_response(index_id, video_id, query, api_key)
            responses["pegasus"] = pegasus_response
        else:
            responses["pegasus"] = "This is a simulated Pegasus response for public videos. To get real responses, please connect your TwelveLabs API key."
    except Exception as e:
        print(f"Error in Pegasus response: {str(e)}")
        responses["pegasus"] = f"Error generating Pegasus response: {str(e)}"

    if selected_model == 'gemini':
        try:
            gemini_response = generate_gemini_response(query, video_path)
            responses["gemini"] = gemini_response
        except Exception as e:
            print(f"Error in Gemini response: {str(e)}")
            responses["gemini"] = f"Error generating Gemini response: {str(e)}"
    elif selected_model == 'gpt4o':
        try:
            gpt4o_response = generate_gpt4o_response(query, video_path)
            responses["gpt4o"] = gpt4o_response
        except Exception as e:
            print(f"Error in GPT-4o response: {str(e)}")
            responses["gpt4o"] = f"Error generating GPT-4o response: {str(e)}"
    
    return jsonify({
        "status": "success", 
        "responses": responses
    })

@app.route('/api/models', methods=['GET'])
def get_available_models():
    models = {
        "pegasus": bool(session.get('twelvelabs_api_key') or TWELVELABS_API_KEY),
        "gemini": bool(session.get('gemini_api_key') or GEMINI_API_KEY),
        "gpt4o": bool(session.get('openai_api_key') or OPENAI_API_KEY)
    }
    
    return jsonify({
        "status": "success", 
        "models": models
    })

if __name__ == '__main__':
    app.run(debug=True)