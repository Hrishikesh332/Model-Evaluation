# Model Evaluation API - Curl Examples

This document contains comprehensive curl examples for all API endpoints with expected responses.

## Base Configuration

```bash
# Base URL for all requests
BASE_URL="http://localhost:5000"
API_BASE="$BASE_URL/api"

# Test API Keys (replace with your actual keys)
TWELVELABS_API_KEY="your_twelvelabs_api_key_here"
GEMINI_API_KEY="your_gemini_api_key_here"
OPENAI_API_KEY="your_openai_api_key_here"

# Test IDs
INDEX_ID="public1"
VIDEO_ID="test_video_123"
```

---

## 1. Health Check

### Command
```bash
curl -X GET "$BASE_URL/health"
```

### Expected Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "components": {
    "cache_manager": "ok",
    "performance_monitor": "ok",
    "scheduler": true,
    "models": {
      "gemini": false,
      "openai": false,
      "twelvelabs": false
    }
  },
  "statistics": {
    "total_comparisons": 0,
    "models_tracked": 0,
    "cache_entries": 0
  }
}
```

---

## 2. Get Available Indexes

### Command
```bash
curl -X GET "$API_BASE/indexes"
```

### Expected Response
```json
{
  "status": "success",
  "indexes": [
    {
      "id": "public1",
      "name": "Dance (Public)",
      "url": "https://playground.twelvelabs.io/indexes/684367740bc747718ef25e2c",
      "index_id": "684367740bc747718ef25e2c"
    },
    {
      "id": "public2",
      "name": "Sports (Public)",
      "url": "https://playground.twelvelabs.io/indexes/67cad6b2f8affe8f9e7b46d0",
      "index_id": "67cad6b2f8affe8f9e7b46d0"
    }
  ],
  "public": true
}
```

---

## 3. Get Available Models

### Command
```bash
curl -X GET "$API_BASE/models"
```

### Expected Response
```json
{
  "status": "success",
  "models": {
    "pegasus": false,
    "gemini": false,
    "gemini-2.5": false,
    "gpt4o": false
  }
}
```

---

## 4. Connect TwelveLabs API

### Command
```bash
curl -X POST "$API_BASE/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "twelvelabs",
    "api_key": "'$TWELVELABS_API_KEY'"
  }'
```

### Expected Response (Success)
```json
{
  "status": "success",
  "message": "TwelveLabs API key connected successfully",
  "indexes": [
    {
      "id": "index_123",
      "name": "My Video Index",
      "video_count": 15
    }
  ]
}
```

### Expected Response (Error)
```json
{
  "status": "error",
  "message": "Invalid API key"
}
```

---

## 5. Connect Gemini API

### Command
```bash
curl -X POST "$API_BASE/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "gemini",
    "api_key": "'$GEMINI_API_KEY'"
  }'
```

### Expected Response (Success)
```json
{
  "status": "success",
  "message": "Gemini API key connected successfully"
}
```

### Expected Response (Error)
```json
{
  "status": "error",
  "message": "Failed to connect: Invalid API key"
}
```

---

## 6. Connect OpenAI API

### Command
```bash
curl -X POST "$API_BASE/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "openai",
    "api_key": "'$OPENAI_API_KEY'"
  }'
```

### Expected Response (Success)
```json
{
  "status": "success",
  "message": "OpenAI API key connected successfully"
}
```

---

## 7. Get Videos in Index

### Command
```bash
curl -X GET "$API_BASE/indexes/$INDEX_ID/videos"
```

### Expected Response
```json
{
  "status": "success",
  "videos": [
    {
      "id": "video_123",
      "name": "Sample Dance Video",
      "duration": 120.5,
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": "video_456",
      "name": "Another Dance Video",
      "duration": 95.2,
      "created_at": "2024-01-15T09:30:00Z"
    }
  ],
  "cached": true
}
```

---

## 8. Select Video

### Command
```bash
curl -X POST "$API_BASE/video/select" \
  -H "Content-Type: application/json" \
  -d '{
    "index_id": "'$INDEX_ID'",
    "video_id": "'$VIDEO_ID'"
  }'
```

### Expected Response (Success)
```json
{
  "status": "success",
  "message": "Video selected successfully",
  "video_id": "test_video_123",
  "video_path": "/path/to/video.mp4"
}
```

### Expected Response (Error)
```json
{
  "status": "error",
  "message": "TwelveLabs API key not found. Please connect your API key to access private videos."
}
```

---

## 9. Get Video Status

### Command
```bash
curl -X GET "$API_BASE/video/status"
```

### Expected Response
```json
{
  "status": "success",
  "video_status": {
    "video_id": "test_video_123",
    "path": "/path/to/video.mp4",
    "exists": true,
    "size": "15.2MB",
    "duration": 120.5
  }
}
```

---

## 10. Analyze Video (Single Model)

### Command
```bash
curl -X POST "$API_BASE/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is happening in this video?",
    "model": "gemini",
    "execution_mode": "sequential",
    "index_id": "your_index_id",
    "video_id": "your_video_id"
  }'
```

### Expected Response
```json
{
  "status": "success",
  "responses": {
    "gemini": "This video shows a person performing a dance routine. The dancer is moving gracefully across the stage with fluid movements and precise choreography. The background appears to be a studio setting with good lighting."
  },
  "performance_data": {
    "gemini": {
      "latency": 2.5,
      "success": true
    }
  },
  "execution_mode": "sequential"
}
```

---

## 11. Analyze Video (Parallel Mode)

### Command
```bash
curl -X POST "$API_BASE/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Describe the main actions in this video",
    "model": "gemini",
    "execution_mode": "parallel",
    "index_id": "your_index_id",
    "video_id": "your_video_id"
  }'
```

### Expected Response
```json
{
  "status": "success",
  "responses": {
    "gemini": "The video shows a dance performance with complex choreography.",
    "pegasus": "A dancer performs a contemporary routine with fluid movements."
  },
  "performance_data": {
    "gemini": {
      "latency": 2.1,
      "success": true
    },
    "pegasus": {
      "latency": 1.8,
      "success": true
    }
  },
  "execution_mode": "parallel",
  "optimization_applied": true
}
```

---

## 12. Compare Models

### Command
```bash
curl -X POST "$API_BASE/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key visual elements?",
    "model": "gemini",
    "compare_models": true,
    "index_id": "your_index_id",
    "video_id": "your_video_id"
  }'
```

### Expected Response
```json
{
  "status": "success",
  "comparison_result": {
    "gemini": {
      "response": "The video contains bright lighting, colorful costumes, and dynamic camera movements.",
      "latency": 2.3,
      "success": true
    },
    "pegasus": {
      "response": "Key visual elements include stage lighting, dance costumes, and choreographed movements.",
      "latency": 1.9,
      "success": true
    }
  },
  "execution_mode": "comparison"
}
```

---

## 13. Get Performance Statistics

### Command
```bash
curl -X GET "$API_BASE/performance/stats"
```

### Expected Response
```json
{
  "status": "success",
  "all_model_stats": {
    "gemini": {
      "total_executions": 25,
      "average_latency": 2.3,
      "min_latency": 1.1,
      "max_latency": 5.2,
      "success_rate": 0.96
    },
    "pegasus": {
      "total_executions": 30,
      "average_latency": 1.8,
      "min_latency": 0.9,
      "max_latency": 3.1,
      "success_rate": 0.98
    }
  },
  "comparison_summary": {
    "models_tracked": 4,
    "total_comparisons": 15,
    "fastest_overall_model": "pegasus"
  }
}
```

---

## 14. Get Performance Statistics (Specific Model)

### Command
```bash
curl -X GET "$API_BASE/performance/stats?model=gemini"
```

### Expected Response
```json
{
  "status": "success",
  "model": "gemini",
  "stats": {
    "total_executions": 25,
    "average_latency": 2.3,
    "min_latency": 1.1,
    "max_latency": 5.2,
    "success_rate": 0.96
  }
}
```

---

## 15. Get Recent Comparisons

### Command
```bash
curl -X GET "$API_BASE/performance/recent-comparisons?limit=5"
```

### Expected Response
```json
{
  "status": "success",
  "recent_comparisons": [
    {
      "timestamp": "2024-01-15T10:25:00Z",
      "query": "What is happening in this video?",
      "models": ["gemini", "pegasus"],
      "latencies": {
        "gemini": 2.1,
        "pegasus": 1.8
      }
    },
    {
      "timestamp": "2024-01-15T10:20:00Z",
      "query": "Describe the main actions",
      "models": ["gemini"],
      "latencies": {
        "gemini": 2.3
      }
    }
  ],
  "count": 2
}
```

---

## 16. Export Performance Data

### Command
```bash
curl -X GET "$API_BASE/performance/export"
```

### Expected Response
```json
{
  "status": "success",
  "performance_data": {
    "model_stats": {
      "gemini": {
        "total_executions": 25,
        "average_latency": 2.3
      }
    },
    "execution_history": [
      {
        "timestamp": "2024-01-15T10:25:00Z",
        "model": "gemini",
        "latency": 2.1,
        "success": true
      }
    ],
    "comparison_data": [
      {
        "timestamp": "2024-01-15T10:25:00Z",
        "models": ["gemini", "pegasus"],
        "latencies": {
          "gemini": 2.1,
          "pegasus": 1.8
        }
      }
    ]
  }
}
```

---

## 17. Clear Performance Statistics

### Command
```bash
curl -X POST "$API_BASE/performance/clear"
```

### Expected Response
```json
{
  "status": "success",
  "message": "Performance statistics cleared successfully"
}
```

---

## 18. Get Cache Statistics

### Command
```bash
curl -X GET "$API_BASE/cache/stats"
```

### Expected Response
```json
{
  "status": "success",
  "cache_stats": {
    "memory_cache": {
      "count": 15,
      "size_mb": 45.2
    },
    "disk_cache": {
      "count": 25,
      "total_size_mb": 150.8
    },
    "hit_rate": 0.78
  }
}
```

---

## 19. Clear All Cache

### Command
```bash
curl -X POST "$API_BASE/clear-cache"
```

### Expected Response
```json
{
  "status": "success",
  "message": "All caches cleared successfully"
}
```

---

## 20. Optimize Cache

### Command
```bash
curl -X POST "$API_BASE/optimize/cache"
```

### Expected Response
```json
{
  "status": "success",
  "optimization_result": {
    "cache_hit_rate": 0.85,
    "memory_usage": "150MB",
    "optimization_suggestions": [
      "Consider increasing memory cache size",
      "Disk cache is 80% full"
    ]
  }
}
```

---

## 21. Preload Popular Videos

### Command
```bash
curl -X POST "$API_BASE/optimize/preload" \
  -H "Content-Type: application/json" \
  -d '{
    "videos": [
      {
        "id": "video_123",
        "path": "/path/to/video1.mp4"
      },
      {
        "id": "video_456",
        "path": "/path/to/video2.mp4"
      }
    ]
  }'
```

### Expected Response
```json
{
  "status": "success",
  "message": "Started preloading 2 videos",
  "preloaded_count": 2
}
```

---

## 22. Preload Video Frames

### Command
```bash
curl -X POST "$API_BASE/preload-frames"
```

### Expected Response
```json
{
  "status": "success",
  "message": "Frames preloaded successfully"
}
```

---

## 23. Load Cached Frames

### Command
```bash
curl -X POST "$API_BASE/load-cached-frames" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "'$VIDEO_ID'",
    "model": "gemini"
  }'
```

### Expected Response (Success)
```json
{
  "status": "success",
  "message": "Frames loaded successfully",
  "frames_loaded": 10,
  "loaded_from_disk": true
}
```

### Expected Response (Not Found)
```json
{
  "status": "error",
  "message": "No cached frames found for this video and model",
  "cached": false
}
```

---

## 24. Get Video Thumbnail

### Command
```bash
curl -X GET "$API_BASE/thumbnails/$INDEX_ID/$VIDEO_ID"
```

### Expected Response
- **Success**: Returns JPEG image data
- **Error**: 
```json
{
  "error": "Thumbnail not found"
}
```

---

## 25. Get Metrics (Prometheus Format)

### Command
```bash
curl -X GET "$BASE_URL/metrics"
```

### Expected Response
```
# HELP model_avg_latency Average latency for each model
# TYPE model_avg_latency gauge
model_avg_latency{model="gemini"} 2.3
model_avg_latency{model="pegasus"} 1.8

# HELP model_total_executions Total executions for each model
# TYPE model_total_executions counter
model_total_executions{model="gemini"} 25
model_total_executions{model="pegasus"} 30

# HELP cache_memory_entries Number of entries in memory cache
# TYPE cache_memory_entries gauge
cache_memory_entries 15

# HELP cache_disk_size_mb Disk cache size in MB
# TYPE cache_disk_size_mb gauge
cache_disk_size_mb 150.8

# HELP total_comparisons Total number of model comparisons
# TYPE total_comparisons counter
total_comparisons 15

# HELP models_tracked Number of models being tracked
# TYPE models_tracked gauge
models_tracked 4
```

---

## 26. Run Benchmark

### Command
```bash
curl -X POST "$BASE_URL/api/benchmark/run" \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": [
      "What is happening in this video?",
      "Describe the main actions and movements.",
      "What are the key visual elements?"
    ],
    "iterations": 3,
    "video_path": "/path/to/test/video.mp4"
  }'
```

### Expected Response
```json
{
  "status": "success",
  "benchmark_results": {
    "gemini": {
      "average_latency": 2.3,
      "min_latency": 1.8,
      "max_latency": 3.1,
      "total_executions": 9,
      "success_rate": 1.0
    },
    "pegasus": {
      "average_latency": 1.7,
      "min_latency": 1.2,
      "max_latency": 2.5,
      "total_executions": 9,
      "success_rate": 1.0
    }
  }
}
```

---

## 27. Auto Optimize

### Command
```bash
curl -X POST "$BASE_URL/api/optimize/auto"
```

### Expected Response
```json
{
  "status": "success",
  "optimization_results": {
    "cache_optimization": {
      "cache_hit_rate": 0.85,
      "memory_usage": "150MB"
    },
    "performance_cleanup": "Cleaned old performance data",
    "frame_cache_cleanup": "Removed 5 old cache entries"
  },
  "message": "Auto-optimization completed successfully"
}
```

---

## Error Responses

All endpoints can return the following error responses:

### 400 Bad Request
```json
{
  "status": "error",
  "message": "Invalid parameters",
  "error_type": "bad_request"
}
```

### 401 Unauthorized
```json
{
  "status": "error",
  "message": "API key required",
  "error_type": "unauthorized"
}
```

### 404 Not Found
```json
{
  "status": "error",
  "message": "Resource not found",
  "error_type": "not_found"
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "message": "Internal server error occurred",
  "error_type": "server_error"
}
```

---

## Complete Workflow Example

Here's a complete workflow example:

```bash
#!/bin/bash

# 1. Check if the API is healthy
echo "1. Checking API health..."
curl -s "$BASE_URL/health" | jq '.'

# 2. Connect API keys
echo "2. Connecting API keys..."
curl -s -X POST "$API_BASE/connect" \
  -H "Content-Type: application/json" \
  -d '{"type": "twelvelabs", "api_key": "'$TWELVELABS_API_KEY'"}' | jq '.'

# 3. Get available indexes
echo "3. Getting available indexes..."
curl -s "$API_BASE/indexes" | jq '.'

# 4. Get videos in an index
echo "4. Getting videos in index..."
curl -s "$API_BASE/indexes/$INDEX_ID/videos" | jq '.'

# 5. Select a video
echo "5. Selecting a video..."
curl -s -X POST "$API_BASE/video/select" \
  -H "Content-Type: application/json" \
  -d '{"index_id": "'$INDEX_ID'", "video_id": "'$VIDEO_ID'"}' | jq '.'

# 6. Analyze the video
echo "6. Analyzing the video..."
curl -s -X POST "$API_BASE/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is happening in this video?", "model": "gemini", "index_id": "'$INDEX_ID'", "video_id": "'$VIDEO_ID'"}' | jq '.'

# 7. Check performance stats
echo "7. Checking performance stats..."
curl -s "$API_BASE/performance/stats" | jq '.'

echo "Workflow completed!"
```

---

## Notes

- Replace placeholder API keys with your actual keys
- The server must be running on `localhost:5000` for these examples to work
- All responses are in JSON format unless specified otherwise
- Use `jq` for pretty-printing JSON responses: `curl ... | jq '.'`
- Session-based authentication is used, so API keys are stored in the session
- Error responses follow a consistent format with `status`, `message`, and `error_type` fields 