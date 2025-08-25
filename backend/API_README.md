# Model Evaluation API Documentation

This directory contains comprehensive API documentation for the Model Evaluation system.

## Documentation Files

### 📖 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
**Complete API documentation** with detailed explanations, examples, and best practices.

**Includes:**
- Full endpoint descriptions
- Request/response examples
- Authentication details
- Error handling
- Performance monitoring
- Caching strategies
- Complete workflow examples

### 📋 [API_REFERENCE.md](./API_REFERENCE.md)
**Quick reference guide** with all endpoints in a concise table format.

**Perfect for:**
- Quick endpoint lookup
- Parameter reference
- Response format checking
- Copy-paste examples

### 🚀 [Model_Evaluation_API.postman_collection.json](./Model_Evaluation_API.postman_collection.json)
**Postman collection** with all API endpoints pre-configured for testing.

**Features:**
- Organized by functionality
- Pre-filled request bodies
- Environment variables
- Ready-to-use examples

## Quick Start

### 1. Setup Environment Variables
```bash
# Create .env file
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
TWELVELABS_API_KEY=your_twelvelabs_api_key
FLASK_SECRET_KEY=your_secret_key
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Test the API

#### Using curl:
```bash
# Connect API key
curl -X POST http://localhost:5000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"type": "twelvelabs", "api_key": "your_key"}'

# Get available indexes
curl http://localhost:5000/api/indexes

# Analyze a video
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is happening?", "model": "gemini"}'
```

#### Using Postman:
1. Import the `Model_Evaluation_API.postman_collection.json` file
2. Set up environment variables in Postman
3. Start testing endpoints

## API Overview

### Core Features
- **Video Analysis**: Analyze videos using multiple AI models
- **Model Comparison**: Compare performance across different models
- **Performance Monitoring**: Track latency, success rates, and usage
- **Caching**: Multi-level caching for improved performance
- **Optimization**: Automatic and manual optimization features

### Supported Models
- **Pegasus (TwelveLabs)**: Video-specific AI model
- **Gemini 1.5 Pro**: Google's multimodal model
- **Gemini 2.5 Pro**: Latest Gemini model
- **GPT-4o**: OpenAI's multimodal model

### Key Endpoints
- `/api/connect` - Connect API keys
- `/api/search` - Analyze videos
- `/api/performance/stats` - Get performance data
- `/api/cache/stats` - Monitor caching
- `/health` - System health check

## Usage Examples

### Basic Video Analysis
```python
import requests

# Connect API
requests.post('http://localhost:5000/api/connect', json={
    'type': 'gemini',
    'api_key': 'your_key'
})

# Analyze video
response = requests.post('http://localhost:5000/api/search', json={
    'query': 'What is happening in this video?',
    'model': 'gemini'
})

print(response.json()['responses']['gemini'])
```

### Model Comparison
```python
# Compare multiple models
response = requests.post('http://localhost:5000/api/search', json={
    'query': 'Describe the main actions',
    'model': 'gemini',
    'compare_models': True
})

# Get performance data
performance = requests.get('http://localhost:5000/api/performance/stats').json()
```

## Performance Monitoring

The API includes comprehensive performance tracking:

- **Latency Monitoring**: Track response times for each model
- **Success Rates**: Monitor success/failure rates
- **Usage Statistics**: Track API usage patterns
- **Comparison Data**: Compare model performance

## Caching System

Multi-level caching for optimal performance:

- **Memory Cache**: Fast access to frequently used data
- **Disk Cache**: Persistent storage for video frames
- **Session Cache**: Temporary storage for user sessions

## Error Handling

All endpoints return consistent error responses:

```json
{
  "status": "error",
  "message": "Error description",
  "error_type": "error_category"
}
```

## Development

### Running in Development Mode
```bash
python app.py
```

### Running with Gunicorn (Production)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Health Check
```bash
curl http://localhost:5000/health
```

### Metrics (Prometheus format)
```bash
curl http://localhost:5000/metrics
```

## Troubleshooting

### Common Issues

1. **API Key Connection Failed**
   - Verify API key is valid
   - Check network connectivity
   - Ensure proper API key format

2. **Video Analysis Fails**
   - Confirm video is selected
   - Check video file exists
   - Verify model API key is connected

3. **Performance Issues**
   - Check cache statistics
   - Monitor system resources
   - Use optimization endpoints

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export FLASK_DEBUG=1
```

## Contributing

When adding new endpoints:

1. Update `API_DOCUMENTATION.md` with full details
2. Add to `API_REFERENCE.md` quick reference
3. Include in Postman collection
4. Update this README if needed

## Support

For issues or questions:
1. Check the comprehensive documentation
2. Review error responses
3. Test with Postman collection
4. Check system health endpoints 