import threading
import time
import concurrent.futures
import os
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass
import queue
import logging
from performance import PerformanceMonitor, ModelPerformance, ComparisonResult

logger = logging.getLogger(__name__)

@dataclass
class ModelTask:
    model_name: str
    model_instance: Any
    prompt: str
    video_path: Optional[str] = None
    video_id: Optional[str] = None
    cache_manager: Optional[Any] = None
    additional_params: Dict = None

class ModelExecutor:
    
    def __init__(self, model_name: str, model_instance: Any, performance_monitor: PerformanceMonitor):
        self.model_name = model_name
        self.model_instance = model_instance
        self.performance_monitor = performance_monitor
        self._lock = threading.Lock()
    
    def execute_task(self, task: ModelTask) -> Tuple[str, ModelPerformance]:

        start_time = time.time()
        success = True
        error_message = None
        response = ""
        response_length = 0
        cache_hit = False
        
        try:
            # Handle different model types with their specific parameter requirements
            if self.model_name == 'pegasus':
                # TwelveLabs service expects: generate_response(video_id, prompt, index_id)
                # We need to get the actual video_id from the task
                actual_video_id = task.video_id if task.video_id else None
                if not actual_video_id and task.video_path:
                    # Extract video_id from video_path if available
                    actual_video_id = task.video_path.split('/')[-1].split('.')[0]
                
                if actual_video_id:
                    response = self.model_instance.generate_response(
                        video_id=actual_video_id,
                        prompt=task.prompt
                    )
                else:
                    raise ValueError("No video_id available for Pegasus model")
            elif self.model_name == 'nova':
                # Nova model expects: analyze_video(video_path, prompt)
                if task.video_path and os.path.exists(task.video_path):
                    response = self.model_instance.analyze_video(task.video_path, task.prompt)
                else:
                    raise ValueError("No valid video file available for Nova model")
            elif hasattr(self.model_instance, 'generate_response'):
                # Other models (Gemini, OpenAI) expect: generate_response(prompt, video_path, ...)
                if task.cache_manager and 'cache_manager' in self.model_instance.generate_response.__code__.co_varnames:
                    response = self.model_instance.generate_response(
                        task.prompt, 
                        task.video_path, 
                        cache_manager=task.cache_manager
                    )
                else:
                    response = self.model_instance.generate_response(task.prompt, task.video_path)
            else:
                raise AttributeError(f"Model {self.model_name} does not have generate_response method")
            
            if isinstance(response, str):
                response_length = len(response)
                
        except Exception as e:
            success = False
            error_message = str(e)
            response = f"Error in {self.model_name}: {str(e)}"
            logger.error(f"Error executing {self.model_name}: {e}")
        
        end_time = time.time()
        latency = end_time - start_time
        
        performance = ModelPerformance(
            model_name=self.model_name,
            start_time=start_time,
            end_time=end_time,
            latency=latency,
            success=success,
            error_message=error_message,
            response=response,
            response_length=response_length,
            cache_hit=cache_hit,
            video_id=task.video_id if hasattr(task, 'video_id') and task.video_id else (task.video_path.split('/')[-1].split('.')[0] if task.video_path else None),
            query=task.prompt
        )
        
        return response, performance

class ParallelModelRunner:
    
    def __init__(self, performance_monitor: PerformanceMonitor, max_workers: int = 4):
        self.performance_monitor = performance_monitor
        self.max_workers = max_workers
        self.executors: Dict[str, ModelExecutor] = {}
        self._results_lock = threading.Lock()
    
    def register_model(self, model_name: str, model_instance: Any):
        self.executors[model_name] = ModelExecutor(
            model_name, model_instance, self.performance_monitor
        )
        logger.info(f"Registered model: {model_name}")
    
    def execute_models_parallel(self, tasks: List[ModelTask], timeout: float = 300.0) -> ComparisonResult:

        start_time = time.time()
        comparison_result = ComparisonResult(parallel_execution=True)
        
        logger.info(f"Starting parallel execution of {len(tasks)} models")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {}
            for task in tasks:
                if task.model_name in self.executors:
                    future = executor.submit(
                        self.executors[task.model_name].execute_task, task
                    )
                    future_to_task[future] = task
                else:
                    logger.warning(f"Model {task.model_name} not registered, skipping")
            
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_task, timeout=timeout):
                try:
                    response, performance = future.result()
                    comparison_result.add_performance(performance)
                    completed_count += 1
                    logger.info(f"Completed {performance.model_name} in {performance.latency:.2f}s")
                    
                except concurrent.futures.TimeoutError:
                    task = future_to_task[future]
                    logger.error(f"Model {task.model_name} timed out")
                    timeout_performance = ModelPerformance(
                        model_name=task.model_name,
                        start_time=start_time,
                        end_time=time.time(),
                        latency=timeout,
                        success=False,
                        error_message="Execution timeout"
                    )
                    comparison_result.add_performance(timeout_performance)
                    
                except Exception as e:
                    task = future_to_task[future]
                    logger.error(f"Error in {task.model_name}: {e}")
                    error_performance = ModelPerformance(
                        model_name=task.model_name,
                        start_time=start_time,
                        end_time=time.time(),
                        latency=0,
                        success=False,
                        error_message=str(e)
                    )
                    comparison_result.add_performance(error_performance)
        
        comparison_result.total_time = time.time() - start_time
        comparison_result.calculate_stats()
        
        logger.info(f"Parallel execution completed in {comparison_result.total_time:.2f}s")
        logger.info(f"Completed {completed_count}/{len(tasks)} models successfully")
        
        return comparison_result
    
    def execute_models_sequential(self, tasks: List[ModelTask]) -> ComparisonResult:
        start_time = time.time()
        comparison_result = ComparisonResult(parallel_execution=False)
        
        logger.info(f"Starting sequential execution of {len(tasks)} models")
        
        for task in tasks:
            if task.model_name in self.executors:
                try:
                    response, performance = self.executors[task.model_name].execute_task(task)
                    comparison_result.add_performance(performance)
                    logger.info(f"Completed {performance.model_name} in {performance.latency:.2f}s")
                except Exception as e:
                    logger.error(f"Error executing {task.model_name}: {e}")
                    error_performance = ModelPerformance(
                        model_name=task.model_name,
                        start_time=time.time(),
                        end_time=time.time(),
                        latency=0,
                        success=False,
                        error_message=str(e)
                    )
                    comparison_result.add_performance(error_performance)
            else:
                logger.warning(f"Model {task.model_name} not registered, skipping")
        
        comparison_result.total_time = time.time() - start_time
        comparison_result.calculate_stats()
        
        logger.info(f"Sequential execution completed in {comparison_result.total_time:.2f}s")
        
        return comparison_result

class OptimizedVideoAnalyzer:
    
    def __init__(self, models_dict: Dict[str, Any], cache_manager: Any, 
                 performance_monitor: PerformanceMonitor, max_workers: int = 4):
        self.models = models_dict
        self.cache_manager = cache_manager
        self.performance_monitor = performance_monitor
        self.parallel_runner = ParallelModelRunner(performance_monitor, max_workers)
        
        for model_name, model_instance in models_dict.items():
            self.parallel_runner.register_model(model_name, model_instance)
        
        logger.info(f"Initialized OptimizedVideoAnalyzer with {len(models_dict)} models")
    
    def analyze_video_parallel(self, query: str, selected_models: List[str], 
                             video_path: Optional[str] = None, 
                             video_id: Optional[str] = None,
                             timeout: float = 300.0) -> Tuple[Dict[str, str], ComparisonResult]:
        
        tasks = []
        for model_name in selected_models:
            if model_name in self.models:
                task = ModelTask(
                    model_name=model_name,
                    model_instance=self.models[model_name],
                    prompt=query,
                    video_path=video_path,
                    video_id=video_id,
                    cache_manager=self.cache_manager
                )
                tasks.append(task)
        
        if not tasks:
            return {}, ComparisonResult()
        
        comparison_result = self.parallel_runner.execute_models_parallel(tasks, timeout)
        
        responses = {}
        for performance in comparison_result.performances:
            if performance.success:
                # Get the actual response from the performance object
                if hasattr(performance, 'response') and performance.response:
                    responses[performance.model_name] = performance.response
                else:
                    responses[performance.model_name] = f"Model executed successfully in {performance.latency:.2f}s"
            else:
                responses[performance.model_name] = f"Error: {performance.error_message}"
        
        self.performance_monitor.add_comparison_result(comparison_result)
        
        return responses, comparison_result
    
    def analyze_video_sequential(self, query: str, selected_models: List[str], 
                               video_path: Optional[str] = None,
                               video_id: Optional[str] = None) -> Tuple[Dict[str, str], ComparisonResult]:

        tasks = []
        for model_name in selected_models:
            if model_name in self.models:
                task = ModelTask(
                    model_name=model_name,
                    model_instance=self.models[model_name],
                    prompt=query,
                    video_path=video_path,
                    video_id=video_id,
                    cache_manager=self.cache_manager
                )
                tasks.append(task)
        
        if not tasks:
            return {}, ComparisonResult()
        
        comparison_result = self.parallel_runner.execute_models_sequential(tasks)
        
        responses = {}
        for performance in comparison_result.performances:
            if performance.success:
                # Get the actual response from the performance object
                if hasattr(performance, 'response') and performance.response:
                    responses[performance.model_name] = performance.response
                else:
                    responses[performance.model_name] = f"Model executed successfully in {performance.latency:.2f}s"
            else:
                responses[performance.model_name] = f"Error: {performance.error_message}"
        
        self.performance_monitor.add_comparison_result(comparison_result)
        
        return responses, comparison_result
    
    def run_model_comparison(self, query: str, video_path: Optional[str] = None, 
                           video_id: Optional[str] = None,
                           include_models: List[str] = None) -> Dict:
        
        if include_models is None:
            include_models = list(self.models.keys())
        
        available_models = [model for model in include_models if model in self.models]
        
        if not available_models:
            return {"error": "No available models for comparison"}
        
        logger.info(f"Running comparison with models: {available_models}")
        
        parallel_responses, parallel_result = self.analyze_video_parallel(
            query, available_models, video_path, video_id
        )
        
        sequential_responses, sequential_result = self.analyze_video_sequential(
            query, available_models, video_path, video_id
        )
        
        parallel_stats = parallel_result.calculate_stats()
        sequential_stats = sequential_result.calculate_stats()
        
        time_saved = sequential_result.total_time - parallel_result.total_time
        speedup_factor = sequential_result.total_time / parallel_result.total_time if parallel_result.total_time > 0 else 0
        
        return {
            "query": query,
            "video_path": video_path,
            "models_compared": available_models,
            "parallel_execution": {
                "responses": parallel_responses,
                "total_time": parallel_result.total_time,
                "stats": parallel_stats
            },
            "sequential_execution": {
                "responses": sequential_responses,
                "total_time": sequential_result.total_time,
                "stats": sequential_stats
            },
            "optimization_benefits": {
                "time_saved_seconds": time_saved,
                "speedup_factor": speedup_factor,
                "efficiency_gain_percent": (time_saved / sequential_result.total_time * 100) if sequential_result.total_time > 0 else 0
            },
            "timestamp": time.time()
        }

class CacheOptimizer:
    
    def __init__(self, cache_manager: Any):
        self.cache_manager = cache_manager
    
    def preload_popular_videos(self, video_ids: List[str], video_paths: List[str]):
        def preload_video(video_id, video_path):
            try:
                if hasattr(self.cache_manager, 'extract_and_cache_frames'):

                    model_suffixes = ['gemini-1.5-pro', 'gemini-2.0-flash', 'gpt4o']
                    for suffix in model_suffixes:
                        cache_key = f"{video_id}_{suffix}"
                        self.cache_manager.extract_and_cache_frames(
                            video_path, num_frames=10, cache_key=cache_key
                        )
                logger.info(f"Preloaded frames for video: {video_id}")
            except Exception as e:
                logger.error(f"Failed to preload video {video_id}: {e}")

        threads = []
        for video_id, video_path in zip(video_ids, video_paths):
            thread = threading.Thread(target=preload_video, args=(video_id, video_path))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        logger.info(f"Completed preloading {len(video_ids)} videos")
    
    def optimize_cache_strategy(self) -> Dict:
        if hasattr(self.cache_manager, 'get_cache_stats'):
            stats = self.cache_manager.get_cache_stats()
            
            recommendations = []
            
            memory_count = stats.get('memory_cache', {}).get('count', 0)
            disk_size_mb = stats.get('disk_cache', {}).get('total_size_mb', 0)
            
            if memory_count > 50:
                recommendations.append("Consider clearing old memory cache entries")
            
            if disk_size_mb > 1000:  # 1GB
                recommendations.append("Disk cache is large, consider cleanup")
            
            return {
                "current_stats": stats,
                "recommendations": recommendations,
                "optimization_applied": True
            }
        
        return {"error": "Cache manager does not support statistics"}