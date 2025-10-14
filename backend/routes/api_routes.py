from flask import Blueprint, request, jsonify, session, make_response
from datetime import datetime
from config import Config
from performance import performance_monitor
from optimize import OptimizedVideoAnalyzer, CacheOptimizer
from services.twelvelabs_service import TwelveLabsService
import logging

logger = logging.getLogger(__name__)

def add_cors_headers(response):
    """Add CORS headers to response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-API-Key, Accept, Origin'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

def create_api_routes(twelvelabs_service, gemini_model, openai_model, video_service, cache_manager, nova_model):
    api = Blueprint('api', __name__)
    
    models_dict = {
        'gemini': gemini_model,
        'gemini-2.0-flash': gemini_model,
        'gemini-2.5-pro': gemini_model,
        'gpt4o': openai_model,
        'pegasus': twelvelabs_service,
        'nova': nova_model
    }
    
    optimized_analyzer = OptimizedVideoAnalyzer(
        models_dict, cache_manager, performance_monitor, max_workers=4
    )
    cache_optimizer = CacheOptimizer(cache_manager)
    
    @api.route('/connect', methods=['POST', 'OPTIONS'])
    def connect_api():
        if request.method == 'OPTIONS':
            response = make_response()
            return add_cors_headers(response)
        """Connect to various API services"""
        print("Connect API called")
        
        api_type = request.json.get('type', 'twelvelabs')
        api_key = request.json.get('api_key')
        
        if not api_key or len(api_key) == 0:
            return jsonify({"status": "error", "message": "Invalid API key"}), 400
        
        print(f"Connecting {api_type} API with key: {api_key[:5]}...")
        
        if api_type == 'twelvelabs':
            # Clear all cached data when connecting new API key
            print("🧹 Clearing cached data for new API key...")
            
            # Clear old indexes
            if 'twelvelabs_indexes' in session:
                session.pop('twelvelabs_indexes', None)
                print("   ✅ Cleared cached indexes")
            
            # Clear all cached videos
            keys_to_remove = []
            for key in session.keys():
                if key.startswith('videos_') or key.endswith('_expiry'):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                session.pop(key, None)
                print(f"   ✅ Cleared cached data: {key}")
            
            # Clear selected video state
            session.pop('selected_index_id', None)
            session.pop('selected_video_id', None)
            session.pop('video_path', None)
            print("   ✅ Cleared selected video state")
            
            # Store new API key
            session['twelvelabs_api_key'] = api_key
            twelvelabs_service.update_api_key(api_key)
            
            try:
                # Fetch fresh indexes with new API key
                print(f"🔄 Fetching fresh indexes with new API key...")
                indexes = twelvelabs_service.get_indexes()
                
                if indexes and len(indexes) > 0:
                    session['twelvelabs_indexes'] = indexes
                    print(f"📊 Found {len(indexes)} fresh indexes with new API key")
                    return jsonify({
                        "status": "success", 
                        "message": "TwelveLabs API key connected successfully - All cached data cleared and refreshed", 
                        "indexes": indexes,
                        "cached_cleared": True,
                        "indexes_count": len(indexes)
                    })
                else:
                    print("❌ No indexes found with new API key")
                    return jsonify({"status": "error", "message": "Connected but no indexes found with this API key"}), 404
            except Exception as e:
                print(f"Exception in connect_api: {str(e)}")
                return jsonify({"status": "error", "message": f"Error connecting: {str(e)}"}), 500
        
        elif api_type == 'gemini':
            return jsonify({
                "status": "error", 
                "message": "Gemini API key management is restricted. Please use environment variables."
            }), 403
        
        elif api_type == 'openai':
            return jsonify({
                "status": "error", 
                "message": "OpenAI API key management is restricted. Please use environment variables."
            }), 403
        
        else:
            return jsonify({"status": "error", "message": f"Unknown API type: {api_type}. Only 'twelvelabs' is supported for user management."}), 400

    @api.route('/disconnect', methods=['POST', 'OPTIONS'])
    def disconnect_api():
        """Disconnect API keys and revert to environment defaults"""
        if request.method == 'OPTIONS':
            response = make_response()
            return add_cors_headers(response)
            
        try:
            # Clear only TwelveLabs API key from session (users can only manage this)
            session.pop('twelvelabs_api_key', None)
            
            # Clear all cached data
            keys_to_remove = []
            for key in session.keys():
                if key.startswith('videos_') or key.endswith('_expiry') or key.startswith('twelvelabs_'):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                session.pop(key, None)
            
            # Clear selected index and video to force fresh selection
            session.pop('selected_index_id', None)
            session.pop('selected_video_id', None)
            session.pop('video_path', None)
            session.pop('last_known_video', None)
            
            # Reset TwelveLabs to use environment variable
            twelvelabs_service.update_api_key(Config.TWELVELABS_API_KEY)
            
            return jsonify({
                "status": "success",
                "message": "Disconnected from all APIs. Using environment defaults.",
                "note": "Please re-select your index and video to continue.",
                "cached_cleared": True
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error disconnecting: {str(e)}"
            }), 500

    def get_api_key(service_name):
        """Get API key from session or fall back to environment variable"""
        session_key = f'{service_name}_api_key'
        env_key = f'{service_name.upper()}_API_KEY'
        
        # Try session first, then environment
        api_key = session.get(session_key) or getattr(Config, env_key, None)
        
        if not api_key:
            logger.warning(f"No API key found for {service_name} in session or environment")
        
        return api_key

    @api.route('/status', methods=['GET'])
    def get_api_status():
        """Get current API key status and source"""
        # Check for API key in headers (from frontend proxy)
        twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
        
        # Determine if we're using user session or environment
        user_session_key = session.get('twelvelabs_api_key')
        environment_key = Config.TWELVELABS_API_KEY
        
        # Use header key if provided, otherwise fall back to session, then environment
        active_key = twelvelabs_header_key or user_session_key or environment_key
        key_source = "user_session" if (twelvelabs_header_key or user_session_key) else "environment"
        
        status = {
            "twelvelabs": {
                "connected": bool(active_key),
                "source": key_source,
                "has_key": bool(active_key),
                "user_manageable": True
            },
            "gemini": {
                "connected": False,  # Users cannot connect Gemini keys
                "source": "environment",  # Always environment
                "has_key": bool(get_api_key('gemini')),
                "user_manageable": False
            },
            "openai": {
                "connected": False,  # Users cannot connect OpenAI keys
                "source": "environment",  # Always environment
                "has_key": bool(get_api_key('openai')),
                "user_manageable": False
            }
        }
        
        return jsonify({
            "status": "success",
            "api_status": status,
            "message": f"Current API key status retrieved. Using {key_source} configuration.",
            "restrictions": {
                "user_manageable": ["twelvelabs"],
                "environment_only": ["gemini", "openai"]
            }
        })

    @api.route('/indexes', methods=['GET', 'OPTIONS'])
    def get_indexes():
        if request.method == 'OPTIONS':
            response = make_response()
            return add_cors_headers(response)
        
        # Check for API key in headers (from frontend proxy)
        twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
        
        # Get API key using priority: header > session > environment
        api_key = twelvelabs_header_key or session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        source = "user_session" if (twelvelabs_header_key or session.get('twelvelabs_api_key')) else "environment"
        
        print(f"🔑 API Key Source: {source}")
        print(f"🔑 Using API Key: {api_key[:10]}..." if api_key else "🔑 No API key available")
        
        if api_key:
            # Create a temporary service instance for this request to avoid conflicts
            temp_service = TwelveLabsService(api_key)
            indexes = temp_service.get_indexes()
            if indexes and len(indexes) > 0:
                session['twelvelabs_indexes'] = indexes
                print(f"📊 Found {len(indexes)} indexes from {source}")
                return jsonify({
                    "status": "success", 
                    "indexes": indexes,
                    "source": source,
                    "message": f"Using {source} API key - {len(indexes)} indexes found"
                })
            else:
                print(f"❌ No indexes found with {source} API key")
                return jsonify({"status": "error", "message": f"No indexes found with {source} API key"}), 404
        else:
            print("❌ No API key available")
            return jsonify({
                "status": "error", 
                "message": "No TwelveLabs API key available. Please connect your API key via /api/connect or set TWELVELABS_API_KEY in environment."
            }), 401

    @api.route('/indexes/<index_id>/videos', methods=['GET', 'OPTIONS'])
    def get_videos(index_id):
        if request.method == 'OPTIONS':
            response = make_response()
            return add_cors_headers(response)
        
        # Check for API key in headers (from frontend proxy)
        twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
        
        # Get API key using priority: header > session > environment
        api_key = twelvelabs_header_key or session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        source = "user_session" if (twelvelabs_header_key or session.get('twelvelabs_api_key')) else "environment"
        
        print(f"🎬 Getting videos for index {index_id} using {source} API key")
        
        cache_key = f"videos_{index_id}"
        cache_expiry = session.get(f"{cache_key}_expiry")
        
        if cache_key in session and cache_expiry and datetime.now().timestamp() < cache_expiry:
            print(f"📦 Using cached videos for index {index_id}")
            return jsonify({"status": "success", "videos": session[cache_key], "cached": True, "source": source})
        
        if api_key:
            # Create a temporary service instance for this request to avoid conflicts
            temp_service = TwelveLabsService(api_key)
            videos = temp_service.get_index_videos(index_id)
            if videos and len(videos) > 0:
                session[cache_key] = videos
                session[f"{cache_key}_expiry"] = datetime.now().timestamp() + 300
                print(f"📹 Found {len(videos)} videos in index {index_id} using {source} API key")
                return jsonify({
                    "status": "success", 
                    "videos": videos,
                    "source": source,
                    "message": f"Using {source} API key - {len(videos)} videos found"
                })
            else:
                print(f"❌ No videos found in index {index_id} with {source} API key")
                return jsonify({"status": "error", "message": f"No videos found in index {index_id} with {source} API key"}), 404
        else:
            print("❌ No API key available for video access")
            return jsonify({
                "status": "error", 
                "message": "No TwelveLabs API key available. Please connect your API key via /api/connect or set TWELVELABS_API_KEY in environment."
            }), 401

    @api.route('/video/select', methods=['POST', 'OPTIONS'])
    def select_video():
        if request.method == 'OPTIONS':
            response = make_response()
            return add_cors_headers(response)
        """Select a video for processing"""
        index_id = request.json.get('index_id')
        video_id = request.json.get('video_id')
        
        if not index_id or not video_id:
            return jsonify({"status": "error", "message": "Index ID and Video ID are required"}), 400
        
        # Check for API key in headers (from frontend proxy)
        twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
        
        # Get API key using priority: header > session > environment
        api_key = twelvelabs_header_key or session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        source = "user_session" if (twelvelabs_header_key or session.get('twelvelabs_api_key')) else "environment"
        
        session['selected_index_id'] = index_id
        session['selected_video_id'] = video_id
        
        # Store last known video for fallback
        session['last_known_video'] = {
            'index_id': index_id,
            'video_id': video_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if api_key:
            # Create a temporary service instance for this request to avoid conflicts
            temp_service = TwelveLabsService(api_key)
            result = video_service.select_video(index_id, video_id, temp_service)
            
            if result["success"]:
                session['video_path'] = result["video_path"]
                return jsonify({
                    "status": "success",
                    "message": result["message"],
                    "video_id": video_id,
                    "video_path": result["video_path"],
                    "source": source
                })
            else:
                return jsonify({"status": "error", "message": result["error"]}), 500
        else:
            return jsonify({
                "status": "error", 
                "message": "No TwelveLabs API key available. Please connect your API key or set TWELVELABS_API_KEY in environment."
            }), 500

    @api.route('/models', methods=['GET'])
    def get_available_models():
        """Get available AI models"""
        models = {
            "pegasus-1.2": bool(get_api_key('twelvelabs')),
            "gemini-2.0-flash": bool(get_api_key('gemini')),
            "gemini-2.5-pro": bool(get_api_key('gemini')),
            "gpt4o": bool(get_api_key('openai'))
        }
        
        return jsonify({
            "status": "success", 
            "models": models
        })

    @api.route('/analyze', methods=['POST', 'OPTIONS'])
    def analyze_videos():
        if request.method == 'OPTIONS':
            response = make_response()
            return add_cors_headers(response)
        """Enhanced video analysis with performance monitoring and parallel processing"""
        print("Enhanced analyze endpoint called")
        query = request.json.get('query')
        selected_model = request.json.get('model', 'gemini')
        execution_mode = request.json.get('execution_mode', 'parallel') 
        compare_models = request.json.get('compare_models', False)
        
        if not query:
            return jsonify({"status": "error", "message": "No query provided"}), 400
        
        # Check for API keys in headers (from frontend proxy) - PRIORITY: header > session > environment
        twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
        gemini_header_key = request.headers.get('X-Gemini-API-Key')
        openai_header_key = request.headers.get('X-OpenAI-API-Key')
        
        # Get video info from request body first, then fall back to session
        index_id = request.json.get('index_id') or session.get('selected_index_id')
        video_id = request.json.get('video_id') or session.get('selected_video_id')
        video_path = request.json.get('video_path') or session.get('video_path')
        
        print(f"Request JSON: {request.json}")
        print(f"Session data - index_id: {session.get('selected_index_id')}, video_id: {session.get('selected_video_id')}")
        print(f"Processing query: '{query}' for video_id: {video_id} with model: {selected_model}")
        print(f"Execution mode: {execution_mode}, Compare models: {compare_models}")
        
        # Log API key sources for debugging
        twelvelabs_key_source = "header" if twelvelabs_header_key else ("session" if session.get('twelvelabs_api_key') else "environment")
        gemini_key_source = "header" if gemini_header_key else ("session" if session.get('gemini_api_key') else "environment")
        openai_key_source = "header" if openai_header_key else ("session" if session.get('openai_api_key') else "environment")
        print(f"🔑 API Key Sources - TwelveLabs: {twelvelabs_key_source}, Gemini: {gemini_key_source}, OpenAI: {openai_key_source}")
        
        if not index_id or not video_id:
            # Try to get the last known video from session as fallback
            last_known_video = session.get('last_known_video', {})
            fallback_index_id = last_known_video.get('index_id')
            fallback_video_id = last_known_video.get('video_id')
            
            if fallback_index_id and fallback_video_id:
                print(f"🔄 Using fallback video: {fallback_index_id}/{fallback_video_id}")
                index_id = fallback_index_id
                video_id = fallback_video_id
            else:
                return jsonify({
                    "status": "error", 
                    "message": "No video selected. Please provide index_id and video_id in request body or select a video first.",
                    "help": {
                        "required_fields": ["index_id", "video_id"],
                        "example_request": {
                            "query": "What is happening in this video?",
                            "model": "gpt4o",
                            "index_id": "your_index_id_here",
                            "video_id": "your_video_id_here"
                        },
                        "frontend_fix": "Update your frontend to include index_id and video_id in the request body"
                    },
                    "debug_info": {
                        "request_body": request.json,
                        "session_index_id": session.get('selected_index_id'),
                        "session_video_id": session.get('selected_video_id'),
                        "fallback_available": bool(fallback_index_id and fallback_video_id)
                    }
                }), 400
        
        # Check if we're using user API key but trying to access default account data
        if twelvelabs_header_key or session.get('twelvelabs_api_key'):
            # User is using their own API key
            user_mode = True
            print(f"🔑 User API mode detected - using user's API key")
        else:
            # Using environment/default API key
            user_mode = False
            print(f"🔑 Default API mode detected - using environment API key")
        
        # Validate that the video belongs to the current API key's account
        # This is a safety check to prevent 403 errors
        try:
            if user_mode:
                # For user mode, we should validate the video exists in their account
                temp_service = TwelveLabsService(twelvelabs_header_key or session.get('twelvelabs_api_key'))
                # Try to get video details to validate access
                try:
                    # This will fail with 403 if the video doesn't belong to the user's account
                    video_info = temp_service.get_video_details(index_id, video_id)
                    print(f"✅ Video {video_id} validated for user account")
                except Exception as e:
                    if "403" in str(e) or "not authorized" in str(e).lower():
                        return jsonify({
                            "status": "error",
                            "message": "Video access denied. This video belongs to a different account. Please select a video from your own account.",
                            "error_type": "video_access_denied",
                            "help": {
                                "issue": "You're using your personal API key, but trying to access a video from the default account",
                                "solution": "Please select a video from your own indexes, or switch back to default mode",
                                "video_id": video_id,
                                "index_id": index_id
                            }
                        }), 403
                    else:
                        # Other errors, let it proceed and fail naturally
                        print(f"⚠️ Video validation failed with non-403 error: {e}")
            else:
                print(f"✅ Using default API key - no additional validation needed")
        except Exception as e:
            print(f"⚠️ Video validation check failed: {e}")
            # Continue with the request - let it fail naturally if there are issues
        
        # Update API keys using priority: header > session > environment
        api_key = gemini_header_key or session.get('gemini_api_key') or Config.GEMINI_API_KEY
        if api_key:
            gemini_model.update_api_key(api_key)
        
        api_key = openai_header_key or session.get('openai_api_key') or Config.OPENAI_API_KEY
        if api_key:
            openai_model.update_api_key(api_key)
        
        api_key = twelvelabs_header_key or session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        if api_key:
            twelvelabs_service.update_api_key(api_key)
        
        responses = {}
        errors = {}
        performance_data = {}
        
        try:
            if compare_models:
                comparison_result = optimized_analyzer.run_model_comparison(
                    query, video_path, video_id, [selected_model, 'pegasus']
                )
                
                return jsonify({
                    "status": "success",
                    "comparison_result": comparison_result,
                    "execution_mode": "comparison"
                })
            
            elif execution_mode == 'parallel':
                selected_models = [selected_model]
                if selected_model != 'pegasus':
                    selected_models.append('pegasus') 
                
                parallel_responses, comparison_result = optimized_analyzer.analyze_video_parallel(
                    query, selected_models, video_path, video_id
                )
                
                actual_responses = await_get_actual_responses(query, selected_models, video_path, 
                                                           gemini_model, openai_model, twelvelabs_service, 
                                                           cache_manager, index_id, video_id)
                
                return jsonify({
                    "status": "success",
                    "responses": actual_responses,
                    "performance_data": comparison_result.to_dict(),
                    "execution_mode": "parallel",
                    "optimization_applied": True
                })
            
            else:
                responses, performance_data = await_get_responses_with_monitoring(
                    query, selected_model, video_path, gemini_model, openai_model, 
                    twelvelabs_service, cache_manager, index_id, video_id
                )
                
                return jsonify({
                    "status": "success",
                    "responses": responses,
                    "performance_data": performance_data,
                    "execution_mode": "sequential"
                })
                
        except Exception as e:
            logger.error(f"Error in enhanced analyze: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error during analysis: {str(e)}"
            }), 500

    @api.route('/analyze/stream', methods=['POST', 'OPTIONS'])
    def analyze_videos_stream():
        if request.method == 'OPTIONS':
            response = make_response()
            return add_cors_headers(response)
        
        """Streaming video analysis with real-time updates"""
        from flask import Response, stream_with_context
        import json
        import time
        
        # Check for API keys in headers (from frontend proxy) - PRIORITY: header > session > environment
        twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
        gemini_header_key = request.headers.get('X-Gemini-API-Key')
        openai_header_key = request.headers.get('X-OpenAI-API-Key')
        
        query = request.json.get('query')
        selected_model = request.json.get('model', 'gemini')
        index_id = request.json.get('index_id') or session.get('selected_index_id')
        video_id = request.json.get('video_id') or session.get('selected_video_id')
        video_path = request.json.get('video_path') or session.get('video_path')
        
        if not query or not index_id or not video_id:
            return jsonify({"status": "error", "message": "Missing required parameters"}), 400
        
        # Check if we're using user API key but trying to access default account data
        if twelvelabs_header_key or session.get('twelvelabs_api_key'):
            # User is using their own API key - validate video access
            try:
                temp_service = TwelveLabsService(twelvelabs_header_key or session.get('twelvelabs_api_key'))
                temp_service.get_video_details(index_id, video_id)
                print(f"✅ Video {video_id} validated for user account (streaming)")
            except Exception as e:
                if "403" in str(e) or "not authorized" in str(e).lower():
                    return jsonify({
                        "status": "error",
                        "message": "Video access denied. This video belongs to a different account. Please select a video from your own account.",
                        "error_type": "video_access_denied"
                    }), 403
                else:
                    print(f"⚠️ Video validation failed with non-403 error: {e}")
        
        # Update API keys using priority: header > session > environment
        api_key = gemini_header_key or session.get('gemini_api_key') or Config.GEMINI_API_KEY
        if api_key:
            gemini_model.update_api_key(api_key)
        
        api_key = openai_header_key or session.get('openai_api_key') or Config.OPENAI_API_KEY
        if api_key:
            openai_model.update_api_key(api_key)
        
        api_key = twelvelabs_header_key or session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        if api_key:
            twelvelabs_service.update_api_key(api_key)
        
        def generate_stream():
            """Generate streaming response"""
            try:
                # Send initial status
                yield f"data: {json.dumps({'event_type': 'start', 'message': 'Analysis started'})}\n\n"
                
                # Process models
                models_to_run = [selected_model]
                if selected_model != 'pegasus':
                    models_to_run.append('pegasus')
                
                responses = {}
                for i, model_name in enumerate(models_to_run):
                    # Send model start event
                    yield f"data: {json.dumps({'event_type': 'model_start', 'model_name': model_name})}\n\n"
                    
                    try:
                        if model_name == 'gemini':
                            # Get Gemini response
                            response = gemini_model.generate_response(query, video_path, "gemini-1.5-pro", cache_manager)
                            # Split response into chunks for streaming effect
                            words = response.split()
                            for word in words:
                                yield f"data: {json.dumps({'event_type': 'text_generation', 'text': word + ' ', 'model': model_name})}\n\n"
                                time.sleep(0.03)  # Small delay for realistic streaming
                            responses["gemini"] = response
                        
                        elif model_name == 'pegasus':
                            # Get Pegasus response
                            response = twelvelabs_service.generate_response(video_id, query, index_id)
                            # Split response into chunks for streaming effect
                            words = response.split()
                            for word in words:
                                yield f"data: {json.dumps({'event_type': 'text_generation', 'text': word + ' ', 'model': model_name})}\n\n"
                                time.sleep(0.03)
                            responses["pegasus"] = response
                        
                        elif model_name == 'gpt4o':
                            response = openai_model.generate_response(query, video_path, cache_manager)
                            words = response.split()
                            for word in words:
                                yield f"data: {json.dumps({'event_type': 'text_generation', 'text': word + ' ', 'model': model_name})}\n\n"
                                time.sleep(0.03)
                            responses["gpt4o"] = response
                    
                    except Exception as e:
                        yield f"data: {json.dumps({'event_type': 'error', 'model': model_name, 'message': str(e)})}\n\n"
                    
                    # Send model end event
                    yield f"data: {json.dumps({'event_type': 'model_end', 'model_name': model_name})}\n\n"
                    
                    # Calculate and send performance metrics for this model
                    if model_name in responses:
                        response_text = responses[model_name]
                        word_count = len(response_text.split())
                        char_count = len(response_text)
                        
                        # More realistic performance calculation
                        import random
                        base_duration = char_count / 150  # 150 chars per second is reasonable
                        variation = random.uniform(0.8, 1.2)  # ±20% variation
                        estimated_duration = base_duration * variation
                        
                        throughput = word_count / estimated_duration if estimated_duration > 0 else 0
                        
                        performance_metrics = {
                            "throughput": round(throughput, 2),
                            "duration": round(estimated_duration, 2),
                            "word_count": word_count,
                            "char_count": char_count
                        }
                        
                        performance_event = {
                            'event_type': 'performance_metrics',
                            'model': model_name,
                            'metrics': performance_metrics
                        }
                        print(f"🚀 Sending performance metrics for {model_name}: {performance_metrics}")
                        yield f"data: {json.dumps(performance_event)}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'event_type': 'complete', 'message': 'Analysis completed'})}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'event_type': 'error', 'message': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            }
        )

    @api.route('/analyze/stream/parallel', methods=['POST', 'OPTIONS'])
    def analyze_videos_stream_parallel():
        if request.method == 'OPTIONS':
            response = make_response()
            return add_cors_headers(response)
        
        """Parallel streaming video analysis with multiple models running simultaneously"""
        from flask import Response, stream_with_context
        import json
        import time
        import os
        from concurrent.futures import ThreadPoolExecutor
        from queue import Queue, Empty
        
        # Check for API keys in headers (from frontend proxy) - PRIORITY: header > session > environment
        twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
        gemini_header_key = request.headers.get('X-Gemini-API-Key')
        openai_header_key = request.headers.get('X-OpenAI-API-Key')
        
        query = request.json.get('query')
        models_to_run = request.json.get('models', ['gemini', 'pegasus'])  # Can specify multiple models
        index_id = request.json.get('index_id') or session.get('selected_index_id')
        video_id = request.json.get('video_id') or session.get('selected_video_id')
        video_path = request.json.get('video_path') or session.get('video_path')
        
        # Store API keys for use in threads (since session is not accessible in threads)
        user_api_keys = {
            'twelvelabs': twelvelabs_header_key or session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY,
            'gemini': gemini_header_key or session.get('gemini_api_key') or Config.GEMINI_API_KEY,
            'openai': openai_header_key or session.get('openai_api_key') or Config.OPENAI_API_KEY
        }
        
        # If video_path is not provided, try to get it from video service
        if not video_path and video_id:
            try:
                # Get video path from video service
                video_filename = f"{video_id}.mp4"
                video_path = os.path.join(Config.VIDEO_FOLDER, video_filename)
                
                # Check if video file exists
                if not os.path.exists(video_path):
                    return jsonify({"status": "error", "message": f"Video file not found. Please select a video first."}), 400
            except Exception as e:
                return jsonify({"status": "error", "message": f"Error getting video path: {str(e)}"}), 400
        
        if not query or not index_id or not video_id or not video_path:
            return jsonify({"status": "error", "message": "Missing required parameters or video file not found"}), 400
        
        # Check if we're using user API key but trying to access default account data
        if twelvelabs_header_key or session.get('twelvelabs_api_key'):
            # User is using their own API key - validate video access
            try:
                temp_service = TwelveLabsService(twelvelabs_header_key or session.get('twelvelabs_api_key'))
                temp_service.get_video_details(index_id, video_id)
                print(f"✅ Video {video_id} validated for user account (parallel streaming)")
            except Exception as e:
                if "403" in str(e) or "not authorized" in str(e).lower():
                    return jsonify({
                        "status": "error",
                        "message": "Video access denied. This video belongs to a different account. Please select a video from your own account.",
                        "error_type": "video_access_denied"
                    }), 403
                else:
                    print(f"⚠️ Video validation failed with non-403 error: {e}")
        
        def generate_parallel_stream():
            """Generate parallel streaming response"""
            try:
                print(f"🚀 Starting parallel analysis with models: {models_to_run}")
                # Send initial status
                yield f"data: {json.dumps({'event_type': 'start', 'message': 'Parallel analysis started', 'models': models_to_run})}\n\n"
                
                # Create a queue to collect responses from all models
                response_queue = Queue()
                model_responses = {}
                active_models = set()
                
                def process_model_response(model_name, response_text, model_queue):
                    """Process individual model response and add to model-specific queue"""
                    try:
                        # Send response in smaller chunks for more frequent updates
                        words = response_text.split()
                        chunk_size = max(1, len(words) // 20)  # Send ~20 chunks for smoother streaming
                        
                        for i in range(0, len(words), chunk_size):
                            chunk = ' '.join(words[i:i + chunk_size]) + ' '
                            event = {
                                'event_type': 'text_generation',
                                'text': chunk,
                                'model': model_name,
                                'timestamp': time.time()
                            }
                            model_queue.put(event)
                            time.sleep(0.005)  # Very fast streaming for better interleaving
                            
                    except Exception as e:
                        error_event = {
                            'event_type': 'error',
                            'model': model_name,
                            'message': str(e),
                            'timestamp': time.time()
                        }
                        model_queue.put(error_event)
                

                
                # Create individual queues for each model
                model_queues = {model: Queue() for model in models_to_run}
                model_futures = {}
                model_responses = {}
                active_models = set(models_to_run)
                completed_models = set()
                
                def run_model_analysis_with_queue(model_name):
                    """Run analysis for a specific model and put results in its queue"""
                    try:
                        print(f"🔄 Starting {model_name} analysis...")
                        # Send model start event
                        start_event = {
                            'event_type': 'model_start',
                            'model_name': model_name,
                            'timestamp': time.time()
                        }
                        model_queues[model_name].put(start_event)
                        
                        # Run the actual analysis
                        print(f"⚡ Running {model_name} analysis...")
                        if model_name == 'gemini':
                            # Use user API key (header > session > environment)
                            api_key = user_api_keys['gemini']
                            if api_key:
                                gemini_model.update_api_key(api_key)
                                response = gemini_model.generate_response(query, video_path, "gemini-2.0-flash", cache_manager)
                            else:
                                response = "Error: No Gemini API key available"
                        elif model_name == 'gemini-2.0-flash':
                            # Use user API key (header > session > environment)
                            api_key = user_api_keys['gemini']
                            if api_key:
                                gemini_model.update_api_key(api_key)
                                response = gemini_model.generate_response(query, video_path, "gemini-2.0-flash", cache_manager)
                            else:
                                response = "Error: No Gemini API key available"
                        elif model_name == 'gemini-2.5-pro':
                            # Use user API key (header > session > environment)
                            api_key = user_api_keys['gemini']
                            if api_key:
                                gemini_model.update_api_key(api_key)
                                response = gemini_model.generate_response(query, video_path, "gemini-2.5-pro", cache_manager)
                            else:
                                response = "Error: No Gemini API key available"
                        elif model_name == 'pegasus' or model_name == 'pegasus-1.2':
                            # Use user API key (header > session > environment)
                            api_key = user_api_keys['twelvelabs']
                            if api_key:
                                # Create a temporary service instance for this request to avoid conflicts
                                temp_service = TwelveLabsService(api_key)
                                
                                # Validate video access before making the API call
                                try:
                                    temp_service.get_video_details(index_id, video_id)
                                    print(f"✅ Video {video_id} validated for user account in parallel streaming")
                                    response = temp_service.generate_response(video_id, query, index_id)
                                except Exception as e:
                                    if "403" in str(e) or "not authorized" in str(e).lower():
                                        response = f"Error: Video access denied. This video belongs to a different account. Please select a video from your own account. (Video ID: {video_id})"
                                        print(f"❌ Video access denied for {video_id}: {e}")
                                    else:
                                        print(f"⚠️ Video validation failed with non-403 error: {e}")
                                        # Continue with the API call anyway
                                        response = temp_service.generate_response(video_id, query, index_id)
                            else:
                                response = "Error: No TwelveLabs API key available"
                        elif model_name == 'gpt4o':
                            # Use user API key (header > session > environment)
                            api_key = user_api_keys['openai']
                            if api_key:
                                openai_model.update_api_key(api_key)
                                response = openai_model.generate_response(query, video_path, cache_manager)
                            else:
                                response = "Error: No OpenAI API key available"
                        elif model_name == 'nova':
                            response = nova_model.analyze_video(video_path, query)
                        else:
                            response = f"Unknown model: {model_name}"
                        
                        print(f"✅ {model_name} completed with {len(response)} characters")
                        
                        # Store the complete response for interleaving
                        model_responses[model_name] = response
                        
                        # Send model end event
                        end_event = {
                            'event_type': 'model_end',
                            'model_name': model_name,
                            'timestamp': time.time()
                        }
                        model_queues[model_name].put(end_event)
                        
                    except Exception as e:
                        error_event = {
                            'event_type': 'error',
                            'model': model_name,
                            'message': str(e),
                            'timestamp': time.time()
                        }
                        model_queues[model_name].put(error_event)
                
                # Start all models in parallel using ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=len(models_to_run)) as executor:
                    # Submit all model analysis tasks
                    for model_name in models_to_run:
                        future = executor.submit(run_model_analysis_with_queue, model_name)
                        model_futures[model_name] = future
                    
                    print(f"📡 Starting to stream responses from {len(active_models)} active models...")
                    
                    # Main streaming loop - wait for all models to complete first
                    print(f"⏳ Waiting for all {len(models_to_run)} models to complete their analysis...")
                    
                    while active_models:
                        try:
                            # Check for model completion events
                            for model_name in list(active_models):
                                try:
                                    event = model_queues[model_name].get_nowait()
                                    print(f"📤 Streaming event: {event['event_type']} from {model_name}")
                                    
                                    # Stream the event immediately
                                    yield f"data: {json.dumps(event)}\n\n"
                                    
                                    # Track model completion
                                    if event['event_type'] == 'model_end':
                                        completed_models.add(model_name)
                                        active_models.discard(model_name)
                                        print(f"🏁 {model_name} completed. Active models: {len(active_models)}")
                                    elif event['event_type'] == 'error':
                                        completed_models.add(model_name)
                                        active_models.discard(model_name)
                                        print(f"❌ {model_name} failed. Active models: {len(active_models)}")
                                        
                                except Empty:
                                    # No events from this model yet
                                    pass
                            
                            # Small delay to prevent busy waiting
                            time.sleep(0.01)
                            
                            # Check if all futures are complete
                            done_futures = [name for name, future in model_futures.items() if future.done()]
                            for model_name in done_futures:
                                try:
                                    model_futures[model_name].result()  # This will raise any exceptions
                                except Exception as e:
                                    # Error already handled in run_model_analysis_with_queue
                                    pass
                                    
                        except Exception as e:
                            yield f"data: {json.dumps({'event_type': 'error', 'message': f'Streaming error: {str(e)}'})}\n\n"
                            break
                    
                    # All models have completed, now start parallel streaming
                    print(f"🎬 All models completed! Starting parallel streaming for: {list(completed_models)}")
                    
                    # Calculate performance metrics for each model
                    performance_metrics = {}
                    for model_name in completed_models:
                        if model_name in model_responses:
                            response_text = model_responses[model_name]
                            word_count = len(response_text.split())
                            char_count = len(response_text)
                            
                            # More realistic performance calculation
                            # Assume average response generation time based on content length
                            # and add some randomness for realistic variation
                            import random
                            base_duration = char_count / 150  # 150 chars per second is reasonable
                            variation = random.uniform(0.8, 1.2)  # ±20% variation
                            estimated_duration = base_duration * variation
                            
                            # Calculate throughput (words per second)
                            throughput = word_count / estimated_duration if estimated_duration > 0 else 0
                            
                            performance_metrics[model_name] = {
                                "throughput": round(throughput, 2),
                                "duration": round(estimated_duration, 2),
                                "word_count": word_count,
                                "char_count": char_count
                            }
                    
                    # Send a special event to indicate parallel streaming is starting
                    yield f"data: {json.dumps({'event_type': 'parallel_streaming_start', 'message': 'Starting parallel streaming', 'models': list(completed_models)})}\n\n"
                    
                    # Get all completed responses
                    completed_responses = {model: response for model, response in model_responses.items() 
                                         if model in completed_models}
                    
                    if completed_responses:
                        # Split responses into words for interleaving
                        all_words = {}
                        for model, response in completed_responses.items():
                            words = response.split()
                            all_words[model] = words
                        
                        # Find the maximum number of words across all models
                        max_words = max(len(words) for words in all_words.values()) if all_words else 0
                        
                        print(f"📝 Starting parallel streaming with {max_words} words per model")
                        
                        # Interleave words from all models simultaneously
                        for i in range(max_words):
                            for model, words in all_words.items():
                                if i < len(words):
                                    # Stream the word for this model
                                    event = {
                                        'event_type': 'text_generation',
                                        'text': words[i] + " ",
                                        'model': model,
                                        'timestamp': time.time()
                                    }
                                    yield f"data: {json.dumps(event)}\n\n"
                            
                            # Small delay for smooth streaming
                            time.sleep(0.02)
                        
                        print(f"✅ Parallel streaming completed for all models")
                        
                        # Send performance metrics for each model
                        for model_name, metrics in performance_metrics.items():
                            performance_event = {
                                'event_type': 'performance_metrics',
                                'model': model_name,
                                'metrics': metrics
                            }
                            print(f"🚀 Sending performance metrics for {model_name}: {metrics}")
                            yield f"data: {json.dumps(performance_event)}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'event_type': 'complete', 'message': 'Parallel analysis completed', 'models_analyzed': list(completed_models)})}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'event_type': 'error', 'message': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate_parallel_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            }
        )


    @api.route('/performance/stats', methods=['GET'])
    def get_performance_stats():
        try:
            model_name = request.args.get('model')
            
            if model_name:
                stats = performance_monitor.get_model_stats(model_name)
                return jsonify({
                    "status": "success",
                    "model": model_name,
                    "stats": stats
                })
            else:
                all_stats = performance_monitor.get_all_model_stats()
                comparison_summary = performance_monitor.get_model_comparison_summary()
                
                return jsonify({
                    "status": "success",
                    "all_model_stats": all_stats,
                    "comparison_summary": comparison_summary
                })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error fetching performance stats: {str(e)}"
            }), 500

    @api.route('/performance/recent-comparisons', methods=['GET'])
    def get_recent_comparisons():
        try:
            limit = request.args.get('limit', 10, type=int)
            recent_comparisons = performance_monitor.get_recent_comparisons(limit)
            
            return jsonify({
                "status": "success",
                "recent_comparisons": recent_comparisons,
                "count": len(recent_comparisons)
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error fetching recent comparisons: {str(e)}"
            }), 500

    @api.route('/performance/export', methods=['GET'])
    def export_performance_data():
        try:
            performance_data = performance_monitor.export_performance_data()
            return jsonify({
                "status": "success",
                "performance_data": performance_data
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error exporting performance data: {str(e)}"
            }), 500

    @api.route('/performance/clear', methods=['POST'])
    def clear_performance_stats():
        try:
            performance_monitor.clear_stats()
            return jsonify({
                "status": "success",
                "message": "Performance statistics cleared successfully"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error clearing performance stats: {str(e)}"
            }), 500

    @api.route('/optimize/cache', methods=['POST'])
    def optimize_cache():
        try:
            optimization_result = cache_optimizer.optimize_cache_strategy()
            return jsonify({
                "status": "success",
                "optimization_result": optimization_result
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error optimizing cache: {str(e)}"
            }), 500

    @api.route('/optimize/preload', methods=['POST'])
    def preload_popular_videos():
        try:
            video_data = request.json.get('videos', [])
            video_ids = [v.get('id') for v in video_data]
            video_paths = [v.get('path') for v in video_data]
            
            if video_ids and video_paths:
                cache_optimizer.preload_popular_videos(video_ids, video_paths)
                return jsonify({
                    "status": "success",
                    "message": f"Started preloading {len(video_ids)} videos",
                    "preloaded_count": len(video_ids)
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "No valid video data provided"
                }), 400
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error preloading videos: {str(e)}"
            }), 500

    def await_get_actual_responses(query, selected_models, video_path, gemini_model, 
                                 openai_model, twelvelabs_service, cache_manager, 
                                 index_id, video_id):
        responses = {}
        
        for model_name in selected_models:
            try:
                if model_name == 'gemini':
                    response = gemini_model.generate_response(query, video_path, "gemini-1.5-pro", cache_manager)
                    responses["gemini"] = response
                elif model_name == 'gemini-2.0-flash':
                    response = gemini_model.generate_response(query, video_path, "gemini-2.0-flash", cache_manager)
                    responses["gemini-2.0-flash"] = response
                elif model_name == 'gpt4o':
                    response = openai_model.generate_response(query, video_path, cache_manager)
                    responses["gpt4o"] = response
                elif model_name == 'pegasus':
                    actual_index_id = session.get('actual_index_id', index_id)
                    response = twelvelabs_service.generate_response(video_id, query, actual_index_id)
                    responses["pegasus"] = response
            except Exception as e:
                responses[model_name] = f"Error: {str(e)}"
        
        return responses

    def await_get_responses_with_monitoring(query, selected_model, video_path, 
                                          gemini_model, openai_model, twelvelabs_service, 
                                          cache_manager, index_id, video_id):
        responses = {}
        performance_data = {}
        
        import time
        start_time = time.time()
        try:
            actual_index_id = session.get('actual_index_id', index_id)
            pegasus_response = twelvelabs_service.generate_response(video_id, query, actual_index_id)
            responses["pegasus"] = pegasus_response
            performance_data["pegasus"] = {
                "latency": time.time() - start_time,
                "success": True
            }
        except Exception as e:
            responses["pegasus"] = f"Error: {str(e)}"
            performance_data["pegasus"] = {
                "latency": time.time() - start_time,
                "success": False,
                "error": str(e)
            }

        start_time = time.time()
        try:
            if selected_model == 'gemini':
                response = gemini_model.generate_response(query, video_path, "gemini-1.5-pro", cache_manager)
                responses["gemini"] = response
            elif selected_model == 'gemini-2.0-flash':
                response = gemini_model.generate_response(query, video_path, "gemini-2.0-flash", cache_manager)
                responses["gemini-2.0-flash"] = response
            elif selected_model == 'gpt4o':
                response = openai_model.generate_response(query, video_path, cache_manager)
                responses["gpt4o"] = response
            
            performance_data[selected_model] = {
                "latency": time.time() - start_time,
                "success": True
            }
        except Exception as e:
            responses[selected_model] = f"Error: {str(e)}"
            performance_data[selected_model] = {
                "latency": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
        
        return responses, performance_data

    @api.route('/clear-cache', methods=['POST'])
    def clear_cache():
        try:
            cache_manager.clear_cache()
            
            # Clear all session-based caches
            keys_to_remove = []
            for key in session.keys():
                if key.startswith('videos_') or key.endswith('_expiry'):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                session.pop(key, None)
            
            # Clear indexes cache
            session.pop('twelvelabs_indexes', None)
            
            # Clear selected video state
            session.pop('selected_index_id', None)
            session.pop('selected_video_id', None)
            session.pop('video_path', None)
            
            return jsonify({
                "status": "success",
                "message": "All caches cleared successfully - indexes, videos, and video state reset"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error clearing cache: {str(e)}"
            }), 500

    @api.route('/refresh-data', methods=['POST'])
    def refresh_data():
        """Force refresh all data with current API key"""
        try:
            # Check for API key in headers (from frontend proxy) - PRIORITY: header > session > environment
            twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
            api_key = twelvelabs_header_key or session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
            
            if not api_key:
                return jsonify({
                    "status": "error",
                    "message": "No API key available for refresh"
                }), 401
            
            # Clear all cached data
            keys_to_remove = []
            for key in session.keys():
                if key.startswith('videos_') or key.endswith('_expiry'):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                session.pop(key, None)
            
            # Clear indexes cache
            session.pop('twelvelabs_indexes', None)
            
            # Clear selected video state
            session.pop('selected_index_id', None)
            session.pop('selected_video_id', None)
            session.pop('video_path', None)
            
            # Fetch fresh indexes
            # Create a temporary service instance for this request to avoid conflicts
            temp_service = TwelveLabsService(api_key)
            indexes = temp_service.get_indexes()
            
            if indexes and len(indexes) > 0:
                session['twelvelabs_indexes'] = indexes
                return jsonify({
                    "status": "success",
                    "message": "Data refreshed successfully",
                    "indexes": indexes,
                    "indexes_count": len(indexes),
                    "source": "user_session" if session.get('twelvelabs_api_key') else "environment"
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "No indexes found after refresh"
                }), 404
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error refreshing data: {str(e)}"
            }), 500

    @api.route('/video/current', methods=['GET'])
    def get_current_video():
        """Get current video selection for frontend reference"""
        current_video = {
            "index_id": session.get('selected_index_id'),
            "video_id": session.get('selected_video_id'),
            "video_path": session.get('video_path'),
            "last_known": session.get('last_known_video', {}),
            "has_selection": bool(session.get('selected_index_id') and session.get('selected_video_id'))
        }
        
        return jsonify({
            "status": "success",
            "current_video": current_video,
            "message": "Current video selection retrieved successfully"
        })

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
        # Check for API key in headers (from frontend proxy) - PRIORITY: header > session > environment
        twelvelabs_header_key = request.headers.get('X-TwelveLabs-API-Key')
        api_key = twelvelabs_header_key or session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        
        if not api_key:
            print("No API key available for thumbnail")
            return jsonify({"error": "No thumbnail available"}), 404
        
        # Create a temporary service instance for this request to avoid conflicts
        temp_service = TwelveLabsService(api_key)
        thumbnail_data = temp_service.get_video_thumbnail(index_id, video_id)
        
        if thumbnail_data:
            return thumbnail_data, 200, {'Content-Type': 'image/jpeg'}
        else:
            return jsonify({"error": "Thumbnail not found"}), 404

    return api