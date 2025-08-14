from flask import Blueprint, request, jsonify, session
from datetime import datetime
from config import Config
from performance import performance_monitor
from optimize import OptimizedVideoAnalyzer, CacheOptimizer
import logging

logger = logging.getLogger(__name__)

def create_api_routes(twelvelabs_service, gemini_model, openai_model, video_service, cache_manager):
    api = Blueprint('api', __name__)
    
    models_dict = {
        'gemini': gemini_model,
        'gemini-2.5': gemini_model,
        'gpt4o': openai_model,
        'pegasus': twelvelabs_service
    }
    
    optimized_analyzer = OptimizedVideoAnalyzer(
        models_dict, cache_manager, performance_monitor, max_workers=4
    )
    cache_optimizer = CacheOptimizer(cache_manager)
    
    @api.route('/connect', methods=['POST'])
    def connect_api():
        """Connect to various API services"""
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
        # First try session API key, then fall back to environment API key
        api_key = session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        
        if api_key:
            twelvelabs_service.update_api_key(api_key)
            indexes = twelvelabs_service.get_indexes()
            if indexes and len(indexes) > 0:
                session['twelvelabs_indexes'] = indexes
                return jsonify({
                    "status": "success", 
                    "indexes": indexes,
                    "source": "session" if session.get('twelvelabs_api_key') else "environment"
                })
            else:
                return jsonify({"status": "error", "message": "No indexes found"}), 404
        else:
            return jsonify({
                "status": "error", 
                "message": "No TwelveLabs API key available. Please connect your API key or set TWELVELABS_API_KEY in environment."
            }), 401

    @api.route('/indexes/<index_id>/videos', methods=['GET'])
    def get_videos(index_id):
        # First try session API key, then fall back to environment API key
        api_key = session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        
        cache_key = f"videos_{index_id}"
        cache_expiry = session.get(f"{cache_key}_expiry")
        
        if cache_key in session and cache_expiry and datetime.now().timestamp() < cache_expiry:
            print(f"Using cached videos for index {index_id}")
            return jsonify({"status": "success", "videos": session[cache_key], "cached": True})
        
        if api_key:
            twelvelabs_service.update_api_key(api_key)
            videos = twelvelabs_service.get_index_videos(index_id)
            if videos and len(videos) > 0:
                session[cache_key] = videos
                session[f"{cache_key}_expiry"] = datetime.now().timestamp() + 300
                return jsonify({
                    "status": "success", 
                    "videos": videos,
                    "source": "session" if session.get('twelvelabs_api_key') else "environment"
                })
            else:
                return jsonify({"status": "error", "message": "No videos found in this index"}), 404
        else:
            return jsonify({
                "status": "error", 
                "message": "No TwelveLabs API key available. Please connect your API key or set TWELVELABS_API_KEY in environment."
            }), 401

    @api.route('/video/select', methods=['POST'])
    def select_video():
        """Select a video for processing"""
        index_id = request.json.get('index_id')
        video_id = request.json.get('video_id')
        
        if not index_id or not video_id:
            return jsonify({"status": "error", "message": "Index ID and Video ID are required"}), 400
        
        # First try session API key, then fall back to environment API key
        api_key = session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY
        
        session['selected_index_id'] = index_id
        session['selected_video_id'] = video_id
        
        if api_key:
            twelvelabs_service.update_api_key(api_key)
            result = video_service.select_video(index_id, video_id, twelvelabs_service)
            
            if result["success"]:
                session['video_path'] = result["video_path"]
                return jsonify({
                    "status": "success",
                    "message": result["message"],
                    "video_id": video_id,
                    "video_path": result["video_path"],
                    "source": "session" if session.get('twelvelabs_api_key') else "environment"
                })
            else:
                return jsonify({"status": "error", "message": result["error"]}), 500
        else:
            return jsonify({
                "status": "error", 
                "message": "No TwelveLabs API key available. Please connect your API key or set TWELVELABS_API_KEY in environment."
            }), 401
        
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
        """Get available AI models"""
        models = {
            "pegasus": bool(session.get('twelvelabs_api_key') or Config.TWELVELABS_API_KEY),
            "gemini": bool(session.get('gemini_api_key') or Config.GEMINI_API_KEY),
            "gemini-2.5": bool(session.get('gemini_api_key') or Config.GEMINI_API_KEY),
            "gpt4o": bool(session.get('openai_api_key') or Config.OPENAI_API_KEY)
        }
        
        return jsonify({"status": "success", "models": models})

    @api.route('/search', methods=['POST'])
    def search_videos():
        """Enhanced search with performance monitoring and parallel processing"""
        print("Enhanced search endpoint called")
        query = request.json.get('query')
        selected_model = request.json.get('model', 'gemini')
        execution_mode = request.json.get('execution_mode', 'parallel') 
        compare_models = request.json.get('compare_models', False)
        
        if not query:
            return jsonify({"status": "error", "message": "No query provided"}), 400
        
        index_id = session.get('selected_index_id')
        video_id = session.get('selected_video_id')
        video_path = session.get('video_path')
        
        print(f"Processing query: '{query}' for video_id: {video_id} with model: {selected_model}")
        print(f"Execution mode: {execution_mode}, Compare models: {compare_models}")
        
        if not index_id or not video_id:
            return jsonify({"status": "error", "message": "No video selected. Please select a video first."}), 400
        
        api_key = session.get('gemini_api_key', Config.GEMINI_API_KEY)
        if api_key:
            gemini_model.update_api_key(api_key)
        
        api_key = session.get('openai_api_key', Config.OPENAI_API_KEY)
        if api_key:
            openai_model.update_api_key(api_key)
        
        api_key = session.get('twelvelabs_api_key', Config.TWELVELABS_API_KEY)
        if api_key:
            twelvelabs_service.update_api_key(api_key)
        
        responses = {}
        errors = {}
        performance_data = {}
        
        try:
            if compare_models:
                comparison_result = optimized_analyzer.run_model_comparison(
                    query, video_path, [selected_model, 'pegasus']
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
                    query, selected_models, video_path
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
            logger.error(f"Error in enhanced search: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error during analysis: {str(e)}"
            }), 500


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
                elif model_name == 'gemini-2.5':
                    response = gemini_model.generate_response(query, video_path, "gemini-2.5-pro-exp-03-25", cache_manager)
                    responses["gemini-2.5"] = response
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
            elif selected_model == 'gemini-2.5':
                response = gemini_model.generate_response(query, video_path, "gemini-2.5-pro-exp-03-25", cache_manager)
                responses["gemini-2.5"] = response
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