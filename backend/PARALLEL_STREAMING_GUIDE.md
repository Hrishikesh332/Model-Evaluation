# Parallel Streaming Implementation Guide

## 🚀 **Overview**
This guide shows how to implement **parallel streaming** where multiple AI models analyze videos simultaneously and stream their responses in real-time. This creates a much faster and more engaging user experience.

## 📡 **New Parallel Streaming Endpoint**

### Endpoint
```
POST /api/analyze/stream/parallel
```

### Request Format
```json
{
  "query": "What is happening in this video?",
  "models": ["gemini", "pegasus", "gpt4o"],  // Specify which models to run
  "index_id": "your_index_id",
  "video_id": "your_video_id",
  "video_path": "path/to/video.mp4" // optional
}
```

### Response Events
- `start` - Parallel analysis begins with list of models
- `model_start` - Each model starts processing
- `text_generation` - Text chunks from any model (includes `model` field)
- `model_end` - Each model finishes
- `complete` - All models complete
- `error` - Error from any model

## 🎯 **Frontend Implementation Examples**

### 1. **React Hook for Parallel Streaming**

```javascript
import { useState, useCallback, useRef } from 'react';

export const useParallelStreaming = () => {
    const [modelTexts, setModelTexts] = useState({});
    const [modelStatus, setModelStatus] = useState({});
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState(null);
    
    const abortControllerRef = useRef(null);

    const startParallelStreaming = useCallback(async (requestData) => {
        try {
            // Reset state
            setIsStreaming(true);
            setModelTexts({});
            setModelStatus({});
            setError(null);
            
            // Initialize model statuses
            const initialStatus = {};
            requestData.models.forEach(model => {
                initialStatus[model] = 'waiting';
            });
            setModelStatus(initialStatus);

            // Create abort controller
            abortControllerRef.current = new AbortController();

            const response = await fetch('/api/analyze/stream/parallel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData),
                signal: abortControllerRef.current.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            setIsStreaming(false);
                            return;
                        }

                        try {
                            const event = JSON.parse(data);
                            handleParallelEvent(event);
                        } catch (e) {
                            console.error('Failed to parse event:', e);
                        }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Streaming cancelled');
            } else {
                setError(error.message);
            }
            setIsStreaming(false);
        }
    }, []);

    const handleParallelEvent = useCallback((event) => {
        switch (event.event_type) {
            case 'start':
                console.log('Parallel analysis started with models:', event.models);
                break;
                
            case 'model_start':
                setModelStatus(prev => ({
                    ...prev,
                    [event.model_name]: 'active'
                }));
                setModelTexts(prev => ({
                    ...prev,
                    [event.model_name]: ''
                }));
                break;
                
            case 'text_generation':
                setModelTexts(prev => ({
                    ...prev,
                    [event.model]: (prev[event.model] || '') + event.text
                }));
                break;
                
            case 'model_end':
                setModelStatus(prev => ({
                    ...prev,
                    [event.model_name]: 'completed'
                }));
                break;
                
            case 'complete':
                setIsStreaming(false);
                break;
                
            case 'error':
                setError(event.message);
                if (event.model) {
                    setModelStatus(prev => ({
                        ...prev,
                        [event.model]: 'error'
                    }));
                }
                break;
        }
    }, []);

    const stopStreaming = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        setIsStreaming(false);
    }, []);

    return {
        modelTexts,
        modelStatus,
        isStreaming,
        error,
        startParallelStreaming,
        stopStreaming
    };
};
```

### 2. **React Component with Side-by-Side Model Display**

```jsx
import React, { useState } from 'react';
import { useParallelStreaming } from './useParallelStreaming';

const ParallelAnalysisInterface = () => {
    const [query, setQuery] = useState('');
    const [selectedModels, setSelectedModels] = useState(['gemini', 'pegasus']);
    
    const {
        modelTexts,
        modelStatus,
        isStreaming,
        error,
        startParallelStreaming,
        stopStreaming
    } = useParallelStreaming();

    const handleStartAnalysis = async () => {
        if (!query.trim()) return;
        
        await startParallelStreaming({
            query: query.trim(),
            models: selectedModels,
            index_id: 'your_index_id', // Replace with actual
            video_id: 'your_video_id'  // Replace with actual
        });
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'waiting': return '#6c757d';
            case 'active': return '#007bff';
            case 'completed': return '#28a745';
            case 'error': return '#dc3545';
            default: return '#6c757d';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'waiting': return '⏳';
            case 'active': return '🔄';
            case 'completed': return '✅';
            case 'error': return '❌';
            default: return '⏳';
        }
    };

    return (
        <div className="parallel-analysis">
            <div className="analysis-header">
                <h1>Parallel AI Analysis</h1>
                <p>Multiple AI models analyze your video simultaneously</p>
            </div>

            <div className="analysis-controls">
                <div className="query-input">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Ask about the video..."
                        disabled={isStreaming}
                    />
                </div>

                <div className="model-selection">
                    <label>Select Models:</label>
                    {['gemini', 'pegasus', 'gpt4o'].map(model => (
                        <label key={model} className="model-checkbox">
                            <input
                                type="checkbox"
                                checked={selectedModels.includes(model)}
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        setSelectedModels(prev => [...prev, model]);
                                    } else {
                                        setSelectedModels(prev => prev.filter(m => m !== model));
                                    }
                                }}
                                disabled={isStreaming}
                            />
                            {model}
                        </label>
                    ))}
                </div>

                <div className="action-buttons">
                    {!isStreaming ? (
                        <button 
                            onClick={handleStartAnalysis}
                            disabled={!query.trim() || selectedModels.length === 0}
                            className="start-btn"
                        >
                            Start Parallel Analysis
                        </button>
                    ) : (
                        <button onClick={stopStreaming} className="stop-btn">
                            Stop Analysis
                        </button>
                    )}
                </div>
            </div>

            {error && (
                <div className="error-message">
                    Error: {error}
                </div>
            )}

            <div className="models-grid">
                {selectedModels.map(model => (
                    <div key={model} className="model-panel">
                        <div className="model-header">
                            <h3>{model.toUpperCase()}</h3>
                            <div 
                                className="status-indicator"
                                style={{ backgroundColor: getStatusColor(modelStatus[model] || 'waiting') }}
                            >
                                {getStatusIcon(modelStatus[model] || 'waiting')}
                                <span>{modelStatus[model] || 'waiting'}</span>
                            </div>
                        </div>
                        
                        <div className="model-content">
                            {modelTexts[model] ? (
                                <div className="text-output">
                                    {modelTexts[model]}
                                    {modelStatus[model] === 'active' && (
                                        <span className="cursor">|</span>
                                    )}
                                </div>
                            ) : (
                                <div className="placeholder">
                                    {modelStatus[model] === 'waiting' && 'Waiting to start...'}
                                    {modelStatus[model] === 'active' && 'Analyzing...'}
                                    {modelStatus[model] === 'completed' && 'Analysis complete!'}
                                    {modelStatus[model] === 'error' && 'Error occurred'}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ParallelAnalysisInterface;
```

### 3. **CSS for Parallel Interface**

```css
.parallel-analysis {
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px;
}

.analysis-header {
    text-align: center;
    margin-bottom: 32px;
}

.analysis-header h1 {
    color: #333;
    margin-bottom: 8px;
}

.analysis-controls {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 32px;
}

.query-input input {
    width: 100%;
    padding: 16px;
    border: 2px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
    margin-bottom: 20px;
}

.query-input input:focus {
    border-color: #007bff;
    outline: none;
}

.model-selection {
    margin-bottom: 20px;
}

.model-selection label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #333;
}

.model-checkbox {
    display: inline-block;
    margin-right: 20px;
    cursor: pointer;
}

.model-checkbox input {
    margin-right: 8px;
}

.action-buttons {
    text-align: center;
}

.start-btn, .stop-btn {
    padding: 14px 28px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.start-btn {
    background: #28a745;
    color: white;
}

.start-btn:hover:not(:disabled) {
    background: #218838;
}

.start-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
}

.stop-btn {
    background: #dc3545;
    color: white;
}

.stop-btn:hover {
    background: #c82333;
}

.models-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 24px;
}

.model-panel {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    overflow: hidden;
}

.model-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
}

.model-header h3 {
    margin: 0;
    color: #333;
    text-transform: capitalize;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 20px;
    color: white;
    font-size: 14px;
    font-weight: 500;
}

.model-content {
    padding: 20px;
    min-height: 300px;
    max-height: 500px;
    overflow-y: auto;
}

.text-output {
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: 'Courier New', monospace;
}

.placeholder {
    text-align: center;
    color: #6c757d;
    margin-top: 120px;
    font-style: italic;
}

.cursor {
    animation: blink 1s infinite;
    color: #007bff;
    font-weight: bold;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

.error-message {
    background: #f8d7da;
    color: #721c24;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 24px;
    border: 1px solid #f5c6cb;
}

/* Responsive Design */
@media (max-width: 768px) {
    .models-grid {
        grid-template-columns: 1fr;
    }
    
    .analysis-controls {
        padding: 16px;
    }
    
    .model-checkbox {
        display: block;
        margin-bottom: 8px;
    }
}
```

### 4. **Vue.js Implementation**

```vue
<template>
  <div class="parallel-analysis-vue">
    <div class="header">
      <h1>Parallel AI Analysis</h1>
      <p>Multiple models working simultaneously</p>
    </div>

    <div class="controls">
      <input 
        v-model="query" 
        placeholder="Enter your question..."
        :disabled="isStreaming"
      />
      
      <div class="model-selector">
        <label v-for="model in availableModels" :key="model">
          <input 
            type="checkbox" 
            :value="model"
            v-model="selectedModels"
            :disabled="isStreaming"
          />
          {{ model }}
        </label>
      </div>

      <button 
        @click="startAnalysis"
        :disabled="!canStart"
        :class="{ 'streaming': isStreaming }"
      >
        {{ isStreaming ? 'Analyzing...' : 'Start Analysis' }}
      </button>
    </div>

    <div class="models-display">
      <div 
        v-for="model in selectedModels" 
        :key="model"
        class="model-card"
        :class="getModelStatus(model)"
      >
        <div class="card-header">
          <h3>{{ model.toUpperCase() }}</h3>
          <span class="status">{{ getModelStatus(model) }}</span>
        </div>
        
        <div class="card-content">
          <div v-if="modelTexts[model]" class="text">
            {{ modelTexts[model] }}
            <span v-if="modelStatus[model] === 'active'" class="cursor">|</span>
          </div>
          <div v-else class="placeholder">
            {{ getPlaceholderText(model) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'ParallelAnalysisVue',
  setup() {
    const query = ref('');
    const selectedModels = ref(['gemini', 'pegasus']);
    const modelTexts = ref({});
    const modelStatus = ref({});
    const isStreaming = ref(false);
    
    const availableModels = ['gemini', 'pegasus', 'gpt4o'];
    
    const canStart = computed(() => {
      return query.value.trim() && selectedModels.value.length > 0 && !isStreaming.value;
    });

    const startAnalysis = async () => {
      if (!canStart.value) return;
      
      isStreaming.value = true;
      modelTexts.value = {};
      modelStatus.value = {};
      
      // Initialize statuses
      selectedModels.value.forEach(model => {
        modelStatus.value[model] = 'waiting';
      });

      try {
        const response = await fetch('/api/analyze/stream/parallel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query.value.trim(),
            models: selectedModels.value,
            index_id: 'your_index_id',
            video_id: 'your_video_id'
          })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                isStreaming.value = false;
                return;
              }

              try {
                const event = JSON.parse(data);
                handleEvent(event);
              } catch (e) {}
            }
          }
        }
      } catch (error) {
        console.error('Analysis failed:', error);
        isStreaming.value = false;
      }
    };

    const handleEvent = (event) => {
      switch (event.event_type) {
        case 'model_start':
          modelStatus.value[event.model_name] = 'active';
          modelTexts.value[event.model_name] = '';
          break;
          
        case 'text_generation':
          if (!modelTexts.value[event.model]) {
            modelTexts.value[event.model] = '';
          }
          modelTexts.value[event.model] += event.text;
          break;
          
        case 'model_end':
          modelStatus.value[event.model_name] = 'completed';
          break;
          
        case 'error':
          if (event.model) {
            modelStatus.value[event.model] = 'error';
          }
          break;
      }
    };

    const getModelStatus = (model) => {
      return modelStatus.value[model] || 'waiting';
    };

    const getPlaceholderText = (model) => {
      const status = getModelStatus(model);
      switch (status) {
        case 'waiting': return 'Waiting to start...';
        case 'active': return 'Analyzing...';
        case 'completed': return 'Analysis complete!';
        case 'error': return 'Error occurred';
        default: return 'Ready';
      }
    };

    return {
      query,
      selectedModels,
      modelTexts,
      modelStatus,
      isStreaming,
      availableModels,
      canStart,
      startAnalysis,
      getModelStatus,
      getPlaceholderText
    };
  }
};
</script>
```

## 🔧 **Advanced Features**

### 1. **Model Performance Comparison**

```javascript
const compareModelPerformance = (modelTexts, modelStatus) => {
    const performance = {};
    
    Object.keys(modelTexts).forEach(model => {
        if (modelStatus[model] === 'completed') {
            const wordCount = modelTexts[model].split(/\s+/).length;
            const charCount = modelTexts[model].length;
            
            performance[model] = {
                wordCount,
                charCount,
                averageWordLength: charCount / wordCount
            };
        }
    });
    
    return performance;
};
```

### 2. **Real-time Progress Tracking**

```javascript
const getOverallProgress = (modelStatus, selectedModels) => {
    const total = selectedModels.length;
    const completed = Object.values(modelStatus).filter(status => 
        status === 'completed' || status === 'error'
    ).length;
    
    return (completed / total) * 100;
};
```

### 3. **Smart Model Selection**

```javascript
const getRecommendedModels = (query) => {
    const recommendations = {
        'gemini': ['gemini', 'pegasus'], // Gemini + Pegasus for general analysis
        'gpt4o': ['gpt4o', 'pegasus'],  // GPT-4 + Pegasus for detailed analysis
        'pegasus': ['pegasus', 'gemini'] // Pegasus + Gemini for video-specific analysis
    };
    
    // Auto-select based on query content
    if (query.toLowerCase().includes('video') || query.toLowerCase().includes('scene')) {
        return recommendations.pegasus;
    } else if (query.toLowerCase().includes('describe') || query.toLowerCase().includes('explain')) {
        return recommendations.gpt4o;
    } else {
        return recommendations.gemini;
    }
};
```

## 📊 **Performance Benefits**

### **Speed Improvement**
- **Sequential**: Model 1 (5s) + Model 2 (3s) + Model 3 (4s) = **12 seconds total**
- **Parallel**: All models simultaneously = **5 seconds total** (fastest model time)

### **User Experience**
- **Immediate feedback** from fastest model
- **Continuous engagement** as models complete
- **Comparison view** of different AI perspectives
- **Faster overall completion**

## 🚨 **Important Considerations**

### **Resource Management**
- Monitor server CPU/memory usage
- Implement rate limiting for parallel requests
- Consider model-specific timeouts

### **Error Handling**
- Individual model failures don't stop others
- Graceful degradation for failed models
- User feedback on partial completions

### **Caching Strategy**
- Cache individual model responses
- Avoid re-running successful models
- Implement smart retry logic

This parallel streaming approach will significantly improve your user experience by providing faster, more engaging video analysis with multiple AI perspectives simultaneously! 