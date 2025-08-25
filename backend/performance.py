import time
import threading
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import statistics
from functools import wraps

@dataclass
class ModelPerformance:

    model_name: str
    start_time: float
    end_time: float
    latency: float
    success: bool
    error_message: Optional[str] = None
    response: Optional[str] = None
    response_length: int = 0
    cache_hit: bool = False
    video_id: Optional[str] = None
    query: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'model_name': self.model_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'latency': self.latency,
            'success': self.success,
            'error_message': self.error_message,
            'response': self.response,
            'response_length': self.response_length,
            'cache_hit': self.cache_hit,
            'video_id': self.video_id,
            'query': self.query,
            'timestamp': datetime.fromtimestamp(self.start_time).isoformat()
        }

@dataclass
class ComparisonResult:

    performances: List[ModelPerformance] = field(default_factory=list)
    total_time: float = 0.0
    fastest_model: Optional[str] = None
    slowest_model: Optional[str] = None
    parallel_execution: bool = False
    
    def add_performance(self, performance: ModelPerformance):
        self.performances.append(performance)
    
    def calculate_stats(self):
        successful_performances = [p for p in self.performances if p.success]
        
        if successful_performances:
            latencies = [p.latency for p in successful_performances]
            self.fastest_model = min(successful_performances, key=lambda x: x.latency).model_name
            self.slowest_model = max(successful_performances, key=lambda x: x.latency).model_name
            
            return {
                'fastest_model': self.fastest_model,
                'slowest_model': self.slowest_model,
                'average_latency': statistics.mean(latencies),
                'median_latency': statistics.median(latencies),
                'latency_std': statistics.stdev(latencies) if len(latencies) > 1 else 0,
                'success_rate': len(successful_performances) / len(self.performances) * 100,
                'total_models': len(self.performances),
                'successful_models': len(successful_performances),
                'parallel_execution': self.parallel_execution,
                'total_time': self.total_time
            }
        return {}
    
    def to_dict(self) -> Dict:
        return {
            'performances': [p.to_dict() for p in self.performances],
            'total_time': self.total_time,
            'stats': self.calculate_stats(),
            'parallel_execution': self.parallel_execution
        }

class PerformanceMonitor:
    
    def __init__(self):
        self.execution_history: List[ComparisonResult] = []
        self.model_stats: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def measure_model_performance(self, model_name: str):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_message = None
                response = None
                response_length = 0
                
                try:
                    response = func(*args, **kwargs)
                    if isinstance(response, str):
                        response_length = len(response)
                except Exception as e:
                    success = False
                    error_message = str(e)
                    response = f"Error in {model_name}: {str(e)}"
                
                end_time = time.time()
                latency = end_time - start_time
                
                # Store performance data
                with self._lock:
                    if model_name not in self.model_stats:
                        self.model_stats[model_name] = []
                    self.model_stats[model_name].append(latency)
                
                # Create performance object
                performance = ModelPerformance(
                    model_name=model_name,
                    start_time=start_time,
                    end_time=end_time,
                    latency=latency,
                    success=success,
                    error_message=error_message,
                    response=response,
                    response_length=response_length
                )
                
                return response, performance
            return wrapper
        return decorator
    
    def get_model_stats(self, model_name: str) -> Dict:
        if model_name not in self.model_stats or not self.model_stats[model_name]:
            return {}
        
        latencies = self.model_stats[model_name]
        return {
            'model_name': model_name,
            'total_executions': len(latencies),
            'average_latency': statistics.mean(latencies),
            'median_latency': statistics.median(latencies),
            'min_latency': min(latencies),
            'max_latency': max(latencies),
            'std_deviation': statistics.stdev(latencies) if len(latencies) > 1 else 0,
            'last_10_avg': statistics.mean(latencies[-10:]) if latencies else 0
        }
    
    def get_all_model_stats(self) -> Dict[str, Dict]:
        return {model: self.get_model_stats(model) for model in self.model_stats.keys()}
    
    def add_comparison_result(self, result: ComparisonResult):

        with self._lock:
            self.execution_history.append(result)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
    
    def get_recent_comparisons(self, limit: int = 10) -> List[Dict]:
        with self._lock:
            recent = self.execution_history[-limit:] if self.execution_history else []
            return [comp.to_dict() for comp in recent]
    
    def get_model_comparison_summary(self) -> Dict:
        all_stats = self.get_all_model_stats()
        
        if not all_stats:
            return {}
        
        # Find best performing models
        avg_latencies = {model: stats['average_latency'] for model, stats in all_stats.items()}
        fastest_overall = min(avg_latencies, key=avg_latencies.get) if avg_latencies else None
        slowest_overall = max(avg_latencies, key=avg_latencies.get) if avg_latencies else None
        
        return {
            'model_stats': all_stats,
            'fastest_overall_model': fastest_overall,
            'slowest_overall_model': slowest_overall,
            'total_comparisons': len(self.execution_history),
            'models_tracked': len(all_stats)
        }
    
    def clear_stats(self):
        with self._lock:
            self.model_stats.clear()
            self.execution_history.clear()
    
    def export_performance_data(self) -> Dict:
        return {
            'model_stats': self.get_all_model_stats(),
            'recent_comparisons': self.get_recent_comparisons(50),
            'summary': self.get_model_comparison_summary(),
            'export_timestamp': datetime.now().isoformat()
        }

class BenchmarkSuite:
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.monitor = performance_monitor
    
    def run_latency_benchmark(self, models_dict: Dict, test_prompts: List[str], 
                            video_path: str = None, iterations: int = 3) -> Dict:
        results = {
            'benchmark_start': datetime.now().isoformat(),
            'iterations': iterations,
            'test_prompts': test_prompts,
            'video_path': video_path,
            'results': []
        }
        
        for prompt in test_prompts:
            for iteration in range(iterations):
                print(f"Running benchmark iteration {iteration + 1}/{iterations} for prompt: {prompt[:50]}...")
                
                comparison_result = ComparisonResult()
                start_time = time.time()
                
                for model_name, model_instance in models_dict.items():
                    try:
                        model_start = time.time()
                        if hasattr(model_instance, 'generate_response'):
                            response = model_instance.generate_response(prompt, video_path)
                        else:
                            response = "Model does not support generate_response method"
                        model_end = time.time()
                        
                        performance = ModelPerformance(
                            model_name=model_name,
                            start_time=model_start,
                            end_time=model_end,
                            latency=model_end - model_start,
                            success=True,
                            response=response,
                            response_length=len(response) if isinstance(response, str) else 0,
                            query=prompt
                        )
                        comparison_result.add_performance(performance)
                        
                    except Exception as e:
                        performance = ModelPerformance(
                            model_name=model_name,
                            start_time=time.time(),
                            end_time=time.time(),
                            latency=0,
                            success=False,
                            error_message=str(e),
                            query=prompt
                        )
                        comparison_result.add_performance(performance)
                
                comparison_result.total_time = time.time() - start_time
                comparison_result.parallel_execution = False
                
                results['results'].append({
                    'prompt': prompt,
                    'iteration': iteration + 1,
                    'comparison': comparison_result.to_dict()
                })
        
        results['benchmark_end'] = datetime.now().isoformat()
        return results
    

performance_monitor = PerformanceMonitor()