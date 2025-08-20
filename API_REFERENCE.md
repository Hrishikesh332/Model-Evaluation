# Model Evaluation API Reference

## Quick Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/connect` | Connect API keys | No |
| GET | `/indexes` | Get available indexes | No |
| GET | `/indexes/{id}/videos` | Get videos in index | No |
| POST | `/video/select` | Select video for processing | No |
| GET | `/models` | Get available models | No |
| POST | `/search` | Analyze video | No |
| GET | `/performance/stats` | Get performance stats | No |
| GET | `/performance/recent-comparisons` | Get recent comparisons | No |
| GET | `/performance/export` | Export performance data | No |
| POST | `/performance/clear` | Clear performance stats | No |
| POST | `/optimize/cache` | Optimize cache | No |
| POST | `/optimize/preload` | Preload videos | No |
| POST | `/clear-cache` | Clear all cache | No |
| GET | `/video/status` | Get video status | No |
| POST | `/preload-frames` | Preload video frames | No |
| GET | `/cache/stats` | Get cache statistics | No |
| POST | `/load-cached-frames` | Load cached frames | No |
| GET | `/thumbnails/{index_id}/{video_id}` | Get video thumbnail | No |

## Endpoint Details

### Authentication Endpoints

#### POST `/connect`
Connect API keys to services.

**Request:**
```json
{
  "type": "twelvelabs|gemini|openai",
  "api_key": "your_api_key"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "API key connected successfully",
  "indexes": [] // TwelveLabs only
}
```

### Video Management

#### GET `/indexes`
Get available video indexes.

**Response:**
```json
{
  "status": "success",
  "indexes": [
    {
      "id": "index_id",
      "name": "Index Name",
      "video_count": 10
    }
  ]
}
```

#### GET `/indexes/{index_id}/videos`
Get videos in specific index.

**Response:**
```json
{
  "status": "success",
  "videos": [
    {
      "id": "video_id",
      "name": "Video Name",
      "duration": 120.5
    }
  ]
}
```

#### POST `/video/select`
Select video for processing.

**Request:**
```json
{
  "index_id": "index_id",
  "video_id": "video_id"
}
```

**Response:**
```json
{
  "status": "success",
  "video_id": "video_id",
  "video_path": "/path/to/video"
}
```

### Model Analysis

#### GET `/models`
Get available AI models.

**Response:**
```json
{
  "status": "success",
  "models": {
    "pegasus": true,
    "gemini": true,
    "gemini-2.5": true,
    "gpt4o": false
  }
}
```

#### POST `/search`
Analyze video with AI models.

**Request:**
```json
{
  "query": "What is happening in this video?",
  "model": "gemini",
  "execution_mode": "parallel|sequential",
  "compare_models": false,
  "index_id": "your_index_id",
  "video_id": "your_video_id",
  "video_path": "optional_video_path"
}
```

**Note:** `index_id` and `video_id` are required. If not provided in request body, the endpoint will fall back to session data.

**Response:**
```json
{
  "status": "success",
  "responses": {
    "gemini": "Analysis result...",
    "pegasus": "Analysis result..."
  },
  "performance_data": {
    "gemini": {"latency": 2.5, "success": true}
  }
}
```

### Performance Monitoring

#### GET `/performance/stats`
Get performance statistics.

**Query Parameters:**
- `model` (optional): Specific model name

**Response:**
```json
{
  "status": "success",
  "all_model_stats": {
    "gemini": {
      "total_executions": 50,
      "average_latency": 2.3,
      "success_rate": 0.98
    }
  }
}
```

#### GET `/performance/recent-comparisons`
Get recent model comparisons.

**Query Parameters:**
- `limit` (optional): Number of results (default: 10)

**Response:**
```json
{
  "status": "success",
  "recent_comparisons": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "query": "What is happening?",
      "latencies": {"gemini": 2.1, "pegasus": 1.8}
    }
  ]
}
```

### Cache Management

#### GET `/cache/stats`
Get cache statistics.

**Response:**
```json
{
  "status": "success",
  "cache_stats": {
    "memory_cache": {"count": 15, "size_mb": 45.2},
    "disk_cache": {"count": 25, "total_size_mb": 150.8},
    "hit_rate": 0.78
  }
}
```

#### POST `/clear-cache`
Clear all cached data.

**Response:**
```json
{
  "status": "success",
  "message": "All caches cleared successfully"
}
```

#### POST `/optimize/cache`
Optimize cache strategy.

**Response:**
```json
{
  "status": "success",
  "optimization_result": {
    "cache_hit_rate": 0.85,
    "memory_usage": "150MB"
  }
}
```

### Video Processing

#### GET `/video/status`
Get selected video status.

**Response:**
```json
{
  "status": "success",
  "video_status": {
    "video_id": "video_id",
    "exists": true,
    "size": "15.2MB",
    "duration": 120.5
  }
}
```

#### POST `/preload-frames`
Preload video frames.

**Response:**
```json
{
  "status": "success",
  "message": "Frames preloaded successfully"
}
```

#### POST `/load-cached-frames`
Load cached frames from disk.

**Request:**
```json
{
  "video_id": "video_id",
  "model": "gemini"
}
```

**Response:**
```json
{
  "status": "success",
  "frames_loaded": 10,
  "loaded_from_disk": true
}
```

### Media

#### GET `/thumbnails/{index_id}/{video_id}`
Get video thumbnail.

**Response:** JPEG image data

## Error Responses

All endpoints return errors in this format:

```json
{
  "status": "error",
  "message": "Error description",
  "error_type": "error_category"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

## Models Available

| Model | Provider | Description | API Key Required |
|-------|----------|-------------|------------------|
| Pegasus | TwelveLabs | Video-specific AI | TwelveLabs |
| Gemini 1.5 Pro | Google | Multimodal AI | Google |
| Gemini 2.5 Pro | Google | Latest Gemini | Google |
| GPT-4o | OpenAI | Multimodal AI | OpenAI |

## Quick Start Example

```bash
# 1. Connect API
curl -X POST http://localhost:5000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"type": "twelvelabs", "api_key": "your_key"}'

# 2. Get indexes
curl http://localhost:5000/api/indexes

# 3. Select video
curl -X POST http://localhost:5000/api/video/select \
  -H "Content-Type: application/json" \
  -d '{"index_id": "index_id", "video_id": "video_id"}'

# 4. Analyze video
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is happening?", "model": "gemini"}'
``` 