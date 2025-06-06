from flask import Blueprint, request, jsonify, session
from datetime import datetime
from config import Config

def create_api_routes(twelvelabs_service, gemini_model, openai_model, video_service, cache_manager):
    api = Blueprint('api', __name__)
    
    @api.route('/connect', methods=['POST'])
    def connect_api():
        print("Connect API called")
        
        api_type = request.json.get('type', 'twelvelabs')
        api_key = request.json.get('api_key')
        
        if not api_key or len(api_key) == 0:
            return jsonify({"status": "error", "message": "Invalid API key"}), 400
        
        print(f"Connecting {api_type} API with key: {api_key[:5]}...")
        
        if api_type == 'twelvelabs':
            session['twelvelabs_api_key'] = api_key
            twelvelabs_service.update_api_key(api_key)
            try:
                indexes = twelvelabs_service.get_indexes()
                if indexes and len(indexes) > 0:
                    session['twelvelabs_indexes'] = indexes
                    return jsonify({
                        "status": "success", 
                        "message": "TwelveLabs API key connected successfully", 
                        "indexes": indexes
                    })
                else:
                    return jsonify({"status": "error", "message": "Connected but no indexes found"}), 404
            except Exception as e:
                print(f"Exception in connect_api: {str(e)}")
                return jsonify({"status": "error", "message": f"Failed to connect: {str(e)}"}), 400
        
        elif api_type == 'gemini':
            session['gemini_api_key'] = api_key
            gemini_model.update_api_key(api_key)
            success, message = gemini_model.test_connection()
            if success:
                return jsonify({"status": "success", "message": "Gemini API key connected successfully"})
            else:
                return jsonify({"status": "error", "message": message}), 400
        
        elif api_type == 'openai':
            session['openai_api_key'] = api_key
            openai_model.update_api_key(api_key)
            success, message = openai_model.test_connection()
            if success:
                return jsonify({"status": "success", "message": "OpenAI API key connected successfully"})
            else:
                return jsonify({"status": "error", "message": message}), 400
        
        else:
            return jsonify({"status": "error", "message": "Invalid API type"}), 400

    @api.route('/indexes', methods=['GET'])
    def get_indexes():
        api_key = session.get('twelvelabs_api_key')
        
        if api_key:
            twelvelabs_service.update_api_key(api_key)
            indexes = twelvelabs_service.get_indexes()
            if indexes and len(indexes) > 0:
                session['twelvelabs_indexes'] = indexes
                return jsonify({"status": "success", "indexes": indexes})
            else:
                return jsonify({"status": "error", "message": "No indexes found"}), 404
        else:
            return jsonify({"status": "success", "indexes": Config.PUBLIC_INDEXES, "public": True})

    @api.route('/indexes/<index_id>/videos', methods=['GET'])
    def get_videos(index_id):
        api_key = session.get('twelvelabs_api_key')
        
        public_index = next((index for index in Config.PUBLIC_INDEXES if index['id'] == index_id), None)
        
        cache_key = f"videos_{index_id}"
        cache_expiry = session.get(f"{cache_key}_expiry")
        
        if cache_key in session and cache_expiry and datetime.now().timestamp() < cache_expiry:
            print(f"Using cached videos for index {index_id}")
            return jsonify({"status": "success", "videos": session[cache_key], "cached": True})
        
        if api_key:
            twelvelabs_service.update_api_key(api_key)
            videos = twelvelabs_service.get_index_videos(index_id)
            if videos and len(videos) > 0:
                # Cache for 5 minutes
                session[cache_key] = videos
                session[f"{cache_key}_expiry"] = datetime.now().timestamp() + 300
                return jsonify({"status": "success", "videos": videos})
            else:
                return jsonify({"status": "error", "message": "No videos found in this index"}), 404
        elif public_index:
            if Config.TWELVELABS_API_KEY:
                actual_index_id = public_index.get('index_id')
                public_service = twelvelabs_service.__class__(Config.TWELVELABS_API_KEY)
                videos = public_service.get_index_videos(actual_index_id)
                if videos and len(videos) > 0:
                    session[cache_key] = videos
                    session[f"{cache_key}_expiry"] = datetime.now().timestamp() + 300
                    return jsonify({"status": "success", "videos": videos, "public": True})
                else:
                    return jsonify({"status": "error", "message": "No videos found in this public index"}), 404
            else:
                return jsonify({"status": "error", "message": "TwelveLabs API key not configured in environment"}), 500
        else:
            return jsonify({"status": "error", "message": "Invalid index ID or TwelveLabs API key required"}), 401

    @api.route('/video/select', methods=['POST'])
    def select_video():

        index_id = request.json.get('index_id')
        video_id = request.json.get('video_id')
        
        if not index_id or not video_id:
            return jsonify({"status": "error", "message": "Index ID and Video ID are required"}), 400
        
        public_index = next((index for index in Config.PUBLIC_INDEXES if index['id'] == index_id), None)
        
        session['selected_index_id'] = index_id
        session['selected_video_id'] = video_id
        
        if public_index:
            if Config.TWELVELABS_API_KEY:
                actual_index_id = public_index.get('index_id')
                session['actual_index_id'] = actual_index_id
                
                public_service = twelvelabs_service.__class__(Config.TWELVELABS_API_KEY)
                result = video_service.select_video(index_id, video_id, public_service, True, actual_index_id)
                
                if result["success"]:
                    session['video_path'] = result["video_path"]
                    return jsonify({
                        "status": "success",
                        "message": result["message"],
                        "video_id": video_id,
                        "video_path": result["video_path"],
                        "public": True
                    })
                else:
                    return jsonify({"status": "error", "message": result["error"]}), 500
            else:
                return jsonify({"status": "error", "message": "TwelveLabs API key not configured in environment"}), 500
        
        api_key = session.get('twelvelabs_api_key')
        if not api_key:
            return jsonify({"status": "error", "message": "TwelveLabs API key not found. Please connect your API key to access private videos."}), 401
        
        twelvelabs_service.update_api_key(api_key)
        result = video_service.select_video(index_id, video_id, twelvelabs_service)
        
        if result["success"]:
            session['video_path'] = result["video_path"]
            return jsonify({
                "status": "success",
                "message": result["message"],
                "video_id": video_id,
                "video_path": result["video_path"]
            })
        else:
            return jsonify({"status": "error", "message": result["error"]}), 500



    @api.route('/models', methods=['GET'])
    def get_available_models():

        models = {
            "pegasus": bool(session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY),
            "gemini": bool(session.get('gemini_api_key') or Config.GEMINI_API_KEY),
            "gemini-2.5": bool(session.get('gemini_api_key') or Config.GEMINI_API_KEY),
            "gpt4o": bool(session.get('openai_api_key') or Config.OPENAI_API_KEY)
        }
        
        return jsonify({"status": "success", "models": models})

    @api.route('/search', methods=['POST'])
    def search_videos():

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
        errors = {}
        
        api_key = session.get('twelvelabs_api_key', Config.TWELVELABS_API_KEY)
        try:
            if api_key:
                actual_index_id = session.get('actual_index_id', index_id)
                twelvelabs_service.update_api_key(api_key)
                pegasus_response = twelvelabs_service.generate_response(video_id, query, actual_index_id)
                responses["pegasus"] = pegasus_response
            else:
                responses["pegasus"] = "This is a simulated Pegasus response for public videos. To get real responses, please connect your TwelveLabs API key."
        except Exception as e:
            print(f"Error in Pegasus response: {str(e)}")
            responses["pegasus"] = f"Error generating Pegasus response: {str(e)}"
            errors["pegasus"] = str(e)

        try:
            if selected_model == 'gemini':
                api_key = session.get('gemini_api_key', Config.GEMINI_API_KEY)
                gemini_model.update_api_key(api_key)
                gemini_response = gemini_model.generate_response(query, video_path, "gemini-1.5-pro", cache_manager)
                responses["gemini"] = gemini_response
                
            elif selected_model == 'gemini-2.5':
                api_key = session.get('gemini_api_key', Config.GEMINI_API_KEY)
                gemini_model.update_api_key(api_key)
                gemini_response = gemini_model.generate_response(query, video_path, "gemini-2.5-pro-exp-03-25", cache_manager)
                responses["gemini-2.5"] = gemini_response
                
            elif selected_model == 'gpt4o':
                api_key = session.get('openai_api_key', Config.OPENAI_API_KEY)
                openai_model.update_api_key(api_key)
                gpt4o_response = openai_model.generate_response(query, video_path, cache_manager)
                responses["gpt4o"] = gpt4o_response
                
        except Exception as e:
            error_message = str(e)
            print(f"Error in {selected_model} response: {error_message}")
            responses[selected_model] = f"Error generating {selected_model} response: {error_message}"
            errors[selected_model] = error_message

        return jsonify({
            "status": "success" if not errors else "partial",
            "responses": responses,
            "errors": errors
        })


    @api.route('/clear-cache', methods=['POST'])
    def clear_cache():
        try:
            cache_manager.clear_cache()
            
            for key in list(session.keys()):
                if key.startswith('videos_') or key.endswith('_expiry'):
                    session.pop(key, None)
            
            return jsonify({
                "status": "success",
                "message": "All caches cleared successfully"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error clearing cache: {str(e)}"
            }), 500



    @api.route('/video/status', methods=['GET'])
    def get_video_status():
        video_id = session.get('selected_video_id')
        video_path = session.get('video_path')
        
        result = video_service.get_video_status(video_id, video_path)
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "video_status": result["video_status"]
            })
        else:
            return jsonify({
                "status": "error",
                "message": result["error"]
            }), 404

    @api.route('/preload-frames', methods=['POST'])
    def preload_frames():

        video_id = session.get('selected_video_id')
        video_path = session.get('video_path')
        
        result = video_service.preload_frames(video_id, video_path)
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "message": result["message"]
            })
        else:
            return jsonify({
                "status": "error",
                "message": result["error"]
            }), 404



    @api.route('/cache/stats', methods=['GET'])
    def get_cache_stats():

        try:
            stats = cache_manager.get_cache_stats()
            return jsonify({
                "status": "success",
                "cache_stats": stats
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error fetching cache statistics: {str(e)}"
            }), 500



    @api.route('/load-cached-frames', methods=['POST'])
    def load_cached_frames_from_disk():

        try:
            video_id = request.json.get('video_id')
            model = request.json.get('model', 'gemini')
            
            if not video_id:
                return jsonify({"status": "error", "message": "No video ID provided"}), 400
            
            result = cache_manager.load_cached_frames_from_disk(video_id, model)
            
            if result["cached"]:
                return jsonify({
                    "status": "success",
                    "message": f"Frames loaded successfully",
                    "frames_loaded": len(result.get("frames", [])),
                    "loaded_from_disk": result.get("loaded_from_disk", False)
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": result.get("error", "Unknown error"),
                    "cached": False
                }), 404
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error loading cached frames: {str(e)}"
            }), 500



    @api.route('/thumbnails/<index_id>/<video_id>')
    def get_video_thumbnail(index_id, video_id):

        api_key = session.get('twelvelabs_api_key', Config.TWELVELABS_API_KEY)
        
        if not api_key:
            print("No API key available for thumbnail")
            return jsonify({"error": "No thumbnail available"}), 404
        
        twelvelabs_service.update_api_key(api_key)
        thumbnail_data = twelvelabs_service.get_video_thumbnail(index_id, video_id)
        
        if thumbnail_data:
            return thumbnail_data, 200, {'Content-Type': 'image/jpeg'}
        else:
            return jsonify({"error": "Thumbnail not found"}), 404

    return api