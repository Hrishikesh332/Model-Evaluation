from flask import Flask, render_template
import atexit
import requests
import os
from datetime import datetime
from config import Config
from cache_manager import CacheManager
from services.twelvelabs_service import TwelveLabsService
from services.video_service import VideoService
from models.gemini_model import GeminiModel
from models.openai_model import OpenAIModel
from routes.api_routes import create_api_routes

from performance import performance_monitor, PerformanceMonitor, BenchmarkSuite
from optimize import OptimizedVideoAnalyzer, CacheOptimizer

from apscheduler.schedulers.background import BackgroundScheduler

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():

    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['VIDEO_FOLDER'] = Config.VIDEO_FOLDER
    app.config['CACHE_FOLDER'] = Config.CACHE_FOLDER

    Config.create_directories()

    cache_manager = CacheManager()
    twelvelabs_service = TwelveLabsService()
    video_service = VideoService(cache_manager)
    gemini_model = GeminiModel()
    openai_model = OpenAIModel()

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
    benchmark_suite = BenchmarkSuite(performance_monitor)

    app.optimized_analyzer = optimized_analyzer
    app.cache_optimizer = cache_optimizer
    app.benchmark_suite = benchmark_suite
    app.performance_monitor = performance_monitor

    api_routes = create_api_routes(
        twelvelabs_service, 
        gemini_model, 
        openai_model, 
        video_service, 
        cache_manager
    )
    app.register_blueprint(api_routes, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/performance-dashboard')
    def performance_dashboard():
        try:
            all_stats = performance_monitor.get_all_model_stats()
            recent_comparisons = performance_monitor.get_recent_comparisons(10)
            comparison_summary = performance_monitor.get_model_comparison_summary()
            
            return render_template('performance_dashboard.html', 
                                 model_stats=all_stats,
                                 recent_comparisons=recent_comparisons,
                                 comparison_summary=comparison_summary)
        except Exception as e:
            logger.error(f"Error loading performance dashboard: {e}")
            return render_template('error.html', error=str(e))

    @app.route('/api/benchmark/run', methods=['POST'])
    def run_benchmark():
        try:
            from flask import request, jsonify
            
            test_prompts = request.json.get('prompts', [
                "What is happening in this video?",
                "Describe the main actions and movements.",
                "What are the key visual elements?"
            ])
            iterations = request.json.get('iterations', 3)
            video_path = request.json.get('video_path')
        
            benchmark_results = benchmark_suite.run_latency_benchmark(
                models_dict, test_prompts, video_path, iterations
            )
            
            return jsonify({
                "status": "success",
                "benchmark_results": benchmark_results
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Benchmark failed: {str(e)}"
            }), 500

    @app.route('/api/optimize/auto', methods=['POST'])
    def auto_optimize():
        try:
            from flask import jsonify
            
            optimization_results = {}
            
            cache_optimization = cache_optimizer.optimize_cache_strategy()
            optimization_results['cache_optimization'] = cache_optimization
            
            if len(performance_monitor.execution_history) > 50:
                performance_monitor.execution_history = performance_monitor.execution_history[-50:]
                optimization_results['performance_cleanup'] = "Cleaned old performance data"
            
            cache_stats = cache_manager.get_cache_stats()
            memory_count = cache_stats.get('memory_cache', {}).get('count', 0)
            
            if memory_count > 20:
                cache_keys = list(cache_manager.video_frames_cache.keys())
                keys_to_remove = cache_keys[:memory_count-20]
                for key in keys_to_remove:
                    cache_manager.video_frames_cache.pop(key, None)
                optimization_results['frame_cache_cleanup'] = f"Removed {len(keys_to_remove)} old cache entries"
            
            return jsonify({
                "status": "success",
                "optimization_results": optimization_results,
                "message": "Auto-optimization completed successfully"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Auto-optimization failed: {str(e)}"
            }), 500

    def wake_up_app():
        try:
            app_url = Config.APP_URL
            if app_url:
                response = requests.get(app_url, timeout=30)
                if response.status_code == 200:
                    logger.info(f"Successfully pinged {app_url}")
                else:
                    logger.warning(f"Failed to ping {app_url} (status: {response.status_code})")
            else:
                logger.debug("APP_URL not configured, skipping ping")
        except Exception as e:
            logger.error(f"Error pinging app: {e}")

    def clean_cache_task():
        try:
            cache_manager.clean_video_cache()
            logger.info("Periodic cache cleanup completed")
        except Exception as e:
            logger.error(f"Error in periodic cache cleanup: {e}")

    def performance_summary_task():
        try:
            summary = performance_monitor.get_model_comparison_summary()
            if summary.get('models_tracked', 0) > 0:
                logger.info(f"Performance Summary - Models tracked: {summary.get('models_tracked')}, "
                          f"Total comparisons: {summary.get('total_comparisons')}, "
                          f"Fastest model: {summary.get('fastest_overall_model')}")
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")

    def auto_optimization_task():
        try:
            if len(performance_monitor.execution_history) > 100:
                performance_monitor.execution_history = performance_monitor.execution_history[-50:]
                logger.info("Cleaned old performance history")
            
            cache_stats = cache_manager.get_cache_stats()
            memory_count = cache_stats.get('memory_cache', {}).get('count', 0)
            disk_size_mb = cache_stats.get('disk_cache', {}).get('total_size_mb', 0)
            
            if memory_count > 30:
                cache_keys = list(cache_manager.video_frames_cache.keys())
                keys_to_remove = cache_keys[:memory_count-20]
                for key in keys_to_remove:
                    cache_manager.video_frames_cache.pop(key, None)
                logger.info(f"Auto-cleaned {len(keys_to_remove)} memory cache entries")
            
            if disk_size_mb > 2000: 
                logger.warning(f"Disk cache size is {disk_size_mb}MB, consider manual cleanup")
                
        except Exception as e:
            logger.error(f"Error in auto-optimization task: {e}")

    scheduler = BackgroundScheduler()
    
    scheduler.add_job(wake_up_app, 'interval', minutes=9, id='wake_up')
    scheduler.add_job(clean_cache_task, 'interval', hours=6, id='cache_cleanup')
    
    scheduler.add_job(performance_summary_task, 'interval', hours=2, id='performance_summary')
    scheduler.add_job(auto_optimization_task, 'interval', hours=4, id='auto_optimization')
    
    try:
        scheduler.start()
        logger.info("Background scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

    atexit.register(lambda: scheduler.shutdown())

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            "status": "error",
            "message": "Internal server error occurred",
            "error_type": "server_error"
        }), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "status": "error",
            "message": "Endpoint not found",
            "error_type": "not_found"
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "status": "error",
            "message": "Bad request",
            "error_type": "bad_request"
        }), 400

    # Health check endpoint
    @app.route('/health')
    def health_check():
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "cache_manager": "ok",
                    "performance_monitor": "ok",
                    "scheduler": scheduler.running if scheduler else False,
                    "models": {
                        "gemini": bool(gemini_model.api_key),
                        "openai": bool(openai_model.api_key),
                        "twelvelabs": bool(twelvelabs_service.api_key)
                    }
                },
                "statistics": {
                    "total_comparisons": len(performance_monitor.execution_history),
                    "models_tracked": len(performance_monitor.model_stats),
                    "cache_entries": len(cache_manager.video_frames_cache)
                }
            }
            
            return jsonify(health_status)
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @app.route('/metrics')
    def metrics():
        try:
            metrics_data = []
            
            for model_name, stats in performance_monitor.get_all_model_stats().items():
                metrics_data.append(f'model_avg_latency{{model="{model_name}"}} {stats.get("average_latency", 0)}')
                metrics_data.append(f'model_total_executions{{model="{model_name}"}} {stats.get("total_executions", 0)}')
                metrics_data.append(f'model_min_latency{{model="{model_name}"}} {stats.get("min_latency", 0)}')
                metrics_data.append(f'model_max_latency{{model="{model_name}"}} {stats.get("max_latency", 0)}')
            
            cache_stats = cache_manager.get_cache_stats()
            metrics_data.append(f'cache_memory_entries {cache_stats.get("memory_cache", {}).get("count", 0)}')
            metrics_data.append(f'cache_disk_size_mb {cache_stats.get("disk_cache", {}).get("total_size_mb", 0)}')
            
            metrics_data.append(f'total_comparisons {len(performance_monitor.execution_history)}')
            metrics_data.append(f'models_tracked {len(performance_monitor.model_stats)}')
            
            return '\n'.join(metrics_data), 200, {'Content-Type': 'text/plain'}
        except Exception as e:
            return f"Error generating metrics: {str(e)}", 500, {'Content-Type': 'text/plain'}

    logger.info("Application created successfully with performance monitoring and optimization")
    return app

def main():
    try:
        app = create_app()
        print("Server Starting...")
        
        if __name__ == '__main__':
            app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
        
        return app
        
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise

app = create_app()

if __name__ == '__main__':
    try:
        logger.info("Starting application in development mode...")
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        raise