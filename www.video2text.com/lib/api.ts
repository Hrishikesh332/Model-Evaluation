const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api"
const NEXT_API_BASE_URL = "/api" // Always use Next.js API routes for client-side operations

export interface ApiResponse<T> {
  status: "success" | "error"
  message?: string
  error_type?: string
  data?: T
  source?: "user_session" | "environment" // Add source tracking
}

export interface Index {
  id: string
  name: string
  video_count: number
}

export interface Video {
  id: string
  name: string
  duration: number
}

export interface ModelStatus {
  pegasus: boolean
  gemini: boolean
  "gemini-2.5": boolean
  gpt4o: boolean
}

export interface SearchResponse {
  responses: Record<string, string>
  performance_data: {
    parallel_execution: boolean
    performances: Array<{
      cache_hit: boolean
      end_time: number
      error_message: string | null
      latency: number
      model_name: string
      query: string
      response_length: number
      start_time: number
      success: boolean
      timestamp: string
      video_id: string
    }>
    stats: {
      average_latency: number
      fastest_model: string
      latency_std: number
      median_latency: number
      parallel_execution: boolean
      slowest_model: string
      success_rate: number
      successful_models: number
      total_models: number
      total_time: number
    }
    total_time: number
  }
  execution_mode: string
  optimization_applied: boolean
  status: "success" | "error"
  source?: "user_session" | "environment"
}

export interface StreamingResponse {
  status: "success" | "error"
  responses: Record<string, string>
  streaming: boolean
  performance_data?: any
}

export interface PerformanceStats {
  all_model_stats: Record<
    string,
    {
      total_executions: number
      average_latency: number
      success_rate: number
    }
  >
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options?.headers as Record<string, string>),
      }

      // Add API key headers if available from cookies
      if (typeof document !== 'undefined') {
        const cookies = document.cookie.split(';').reduce((acc, cookie) => {
          const [key, value] = cookie.trim().split('=')
          acc[key] = value
          return acc
        }, {} as Record<string, string>)

        if (cookies.twelvelabs_api_key) {
          headers['X-TwelveLabs-API-Key'] = cookies.twelvelabs_api_key
        }
        if (cookies.gemini_api_key) {
          headers['X-Gemini-API-Key'] = cookies.gemini_api_key
        }
        if (cookies.openai_api_key) {
          headers['X-OpenAI-API-Key'] = cookies.openai_api_key
        }
      }

      const url = `${API_BASE_URL}${endpoint}`
      console.log(`Making API request to: ${url}`)
      
      const response = await fetch(url, {
        headers,
        ...options,
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`API request failed: ${response.status} ${response.statusText}`, errorText)
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
      }

      const data = await response.json()

      if (data.status === "error") {
        throw new Error(data.message || "API request failed")
      }

      return data
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error)
      throw error
    }
  }

  // Helper method for requests with custom base URL
  private async requestWithBaseUrl<T>(baseUrl: string, endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options?.headers as Record<string, string>),
      }

      const url = `${baseUrl}${endpoint}`
      console.log(`Making API request to: ${url}`)
      
      const response = await fetch(url, {
        headers,
        ...options,
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`API request failed: ${response.status} ${response.statusText}`, errorText)
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
      }

      const data = await response.json()

      if (data.status === "error") {
        throw new Error(data.message || "API request failed")
      }

      return data
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error)
      throw error
    }
  }

  // Authentication
  async connectApiKey(type: "twelvelabs" | "gemini" | "openai", apiKey: string) {
    return this.requestWithBaseUrl(NEXT_API_BASE_URL, "/connect", {
      method: "POST",
      body: JSON.stringify({ type, api_key: apiKey }),
    })
  }


  // Video Management
  async getIndexes(): Promise<{ indexes: Index[]; source?: string; message?: string }> {
    const response = await this.requestWithBaseUrl(NEXT_API_BASE_URL, `/indexes?t=${Date.now()}`) as any
    console.log("getIndexes raw response:", response)

    // Handle different response formats from the API
    if (Array.isArray(response)) {
      return { indexes: response }
    } else if (response && Array.isArray(response.data)) {
      return { indexes: response.data, source: response.source, message: response.message }
    } else if (response && Array.isArray(response.indexes)) {
      return response
    } else {
      console.error("Unexpected indexes response format:", response)
      throw new Error("Invalid response format from indexes API")
    }
  }

  async getVideos(indexId: string): Promise<{ videos: Video[]; source?: string; message?: string }> {
    const response = await this.requestWithBaseUrl(NEXT_API_BASE_URL, `/indexes/${indexId}/videos?t=${Date.now()}`) as any
    console.log("getVideos raw response:", response)

    // Handle different response formats from the API
    if (Array.isArray(response)) {
      return { videos: response }
    } else if (response && Array.isArray(response.data)) {
      return { videos: response.data, source: response.source, message: response.message }
    } else if (response && Array.isArray(response.videos)) {
      return response
    } else {
      console.error("Unexpected videos response format:", response)
      throw new Error("Invalid response format from videos API")
    }
  }

  async selectVideo(indexId: string, videoId: string) {
    return this.requestWithBaseUrl(NEXT_API_BASE_URL, "/video/select", {
      method: "POST",
      body: JSON.stringify({ index_id: indexId, video_id: videoId }),
    })
  }

  // Model Management
  async getModels(): Promise<{ models: ModelStatus; source?: string; message?: string }> {
    return this.requestWithBaseUrl(NEXT_API_BASE_URL, "/models")
  }

  // Search and Analysis
  async analyzeVideo(
    query: string,
    model: string,
    execution_mode: "parallel" | "sequential" = "sequential",
    compare_models = false,
    indexId?: string,
    videoId?: string,
    onStreamUpdate?: (text: string, modelName: string, performanceData?: any) => void,
    onStreamComplete?: (modelName: string, finalPerformanceData?: any) => void,
  ): Promise<SearchResponse | StreamingResponse> {
    // Try streaming endpoint first - use Next.js API route to ensure user API keys are passed
    try {
      const streamResponse = await fetch(`${NEXT_API_BASE_URL}/analyze/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          query,
          model,
          execution_mode,
          compare_models,
          index_id: indexId,
          video_id: videoId,
        }),
      })

      if (streamResponse.ok && streamResponse.headers.get("content-type")?.includes("text/event-stream")) {
        console.log("Using streaming endpoint")
        return this.handleStreamingResponse(streamResponse, onStreamUpdate, onStreamComplete)
      }
    } catch (error) {
      console.log("Streaming endpoint failed, falling back to regular endpoint:", error)
    }

    // Fallback to regular endpoint - use Next.js API route to ensure user API keys are passed
    const response = await fetch(`${NEXT_API_BASE_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream", // Request streaming format
      },
      body: JSON.stringify({
        query,
        model,
        execution_mode,
        compare_models,
        index_id: indexId,
        video_id: videoId,
        stream: true, // Request streaming
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // Check if response is streaming
    const contentType = response.headers.get("content-type")
    if (contentType && contentType.includes("text/event-stream")) {
              console.log("Regular endpoint returned streaming response")
      return this.handleStreamingResponse(response, onStreamUpdate, onStreamComplete)
    } else {
              console.log("Using regular JSON response")
      const data = await response.json()
      if (data.status === "error") {
        throw new Error(data.message || "API request failed")
      }
      return data
    }
  }

  async analyzeVideoParallel(
    query: string,
    models: string[],
    execution_mode: "parallel" | "sequential" = "parallel",
    compare_models = true,
    indexId?: string,
    videoId?: string,
    onStreamUpdate?: (text: string, modelName: string, performanceData?: any) => void,
    onStreamComplete?: (modelName: string, finalPerformanceData?: any) => void,
  ): Promise<SearchResponse | StreamingResponse> {
    console.log("analyzeVideoParallel called with models:", models)
    console.log("Attempting parallel streaming endpoint via Next.js API route:", `${NEXT_API_BASE_URL}/analyze/stream/parallel`)

    // Try parallel streaming endpoint via Next.js API route (which handles user API keys)
    try {
      const streamResponse = await fetch(`${NEXT_API_BASE_URL}/analyze/stream/parallel`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          query,
          models,
          execution_mode,
          compare_models,
          index_id: indexId,
          video_id: videoId,
        }),
      })

      console.log("Parallel streaming response status:", streamResponse.status)
      console.log("Parallel streaming response content-type:", streamResponse.headers.get("content-type"))

      if (streamResponse.ok && streamResponse.headers.get("content-type")?.includes("text/event-stream")) {
        console.log("✅ Successfully using parallel streaming endpoint with models:", models)
        return this.handleParallelStreamingResponse(streamResponse, onStreamUpdate, onStreamComplete)
      } else {
        console.log("❌ Parallel streaming endpoint failed or returned non-streaming response")
      }
    } catch (error) {
      console.log("❌ Parallel streaming endpoint failed with error:", error)
    }

    console.log("⚠️ Falling back to single model streaming with first model:", models[0])
    // Fallback to regular streaming with first model
    return this.analyzeVideo(query, models[0], execution_mode, compare_models, indexId, videoId, onStreamUpdate)
  }

  private async handleStreamingResponse(
    response: Response,
    onStreamUpdate?: (text: string, modelName: string, performanceData?: any) => void,
    onStreamComplete?: (modelName: string, finalPerformanceData?: any) => void,
  ): Promise<StreamingResponse> {
    return new Promise((resolve, reject) => {
      const reader = response.body?.getReader()
      if (!reader) {
        reject(new Error("No response body reader available"))
        return
      }

      const decoder = new TextDecoder()
      let buffer = ""
      const responses: Record<string, string> = {}
      const modelTexts: Record<string, string> = {}
      let performanceData: any = null
      let isComplete = false

      function processStream() {
        reader!
          .read()
          .then(({ done, value }) => {
            if (done) {
              if (!isComplete) {
                resolve({
                  status: "success",
                  responses: responses,
                  streaming: true,
                  performance_data: performanceData,
                })
              }
              return
            }

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split("\n")
            buffer = lines.pop() || ""

            for (const line of lines) {
              if (line.trim() === "") continue

              if (line.startsWith("data: ")) {
                const dataStr = line.slice(6).trim()

                if (dataStr === "[DONE]") {
                  isComplete = true
                  resolve({
                    status: "success",
                    responses: modelTexts,
                    streaming: true,
                    performance_data: performanceData,
                  })
                  return
                }

                try {
                  const data = JSON.parse(dataStr)
                  console.log("Streaming event:", data.event_type, data.model || "unknown")

                  switch (data.event_type) {
                    case "start":
                      console.log("Analysis started")
                      break

                    case "model_start":
                      const modelName = data.model_name || data.model
                      if (modelName) {
                        modelTexts[modelName] = ""
                        console.log(`Model ${modelName} started`)
                      }
                      break

                    case "text_generation":
                      const textModel = data.model || data.model_name
                      const textChunk = data.text || ""

                      if (textModel && textChunk) {
                        if (!modelTexts[textModel]) {
                          modelTexts[textModel] = ""
                        }
                        modelTexts[textModel] += textChunk

                        // Update UI immediately with streaming text
                        if (onStreamUpdate) {
                          onStreamUpdate(modelTexts[textModel], textModel, performanceData)
                        }
                      }
                      break

                    case "model_end":
                      const endModel = data.model_name || data.model
                      if (endModel && modelTexts[endModel]) {
                        responses[endModel] = modelTexts[endModel]
                        console.log(`Model ${endModel} completed`)
                      }
                      break

                    case "complete":
                      // Copy all model texts to final responses
                      Object.assign(responses, modelTexts)
                      isComplete = true
                      resolve({
                        status: "success",
                        responses: responses,
                        streaming: true,
                        performance_data: performanceData,
                      })
                      return

                    case "performance_data":
                      performanceData = data.data || data
                      break

                    case "performance_metrics":
                      // Store performance metrics for specific model
                      if (!performanceData) {
                        performanceData = {}
                      }
                      if (data.model && data.metrics) {
                        performanceData[data.model] = data.metrics
                        console.log(`Performance metrics for ${data.model}:`, data.metrics)
                        
                        // Call completion callback with performance data
                        if (onStreamComplete) {
                          onStreamComplete(data.model, data.metrics)
                        }
                      }
                      break

                    case "error":
                      reject(new Error(data.message || "Streaming error"))
                      return
                  }
                } catch (e) {
                  console.warn("Failed to parse streaming data:", e, "Raw data:", dataStr)
                }
              }
            }

            processStream()
          })
          .catch(reject)
      }

      processStream()
    })
  }

  private async handleParallelStreamingResponse(
    response: Response,
    onStreamUpdate?: (text: string, modelName: string, performanceData?: any) => void,
    onStreamComplete?: (modelName: string, finalPerformanceData?: any) => void,
  ): Promise<StreamingResponse> {
    return new Promise((resolve, reject) => {
      const reader = response.body?.getReader()
      if (!reader) {
        reject(new Error("No response body reader available"))
        return
      }

      const decoder = new TextDecoder()
      let buffer = ""
      const responses: Record<string, string> = {}
      const modelTexts: Record<string, string> = {}
      const modelStatus: Record<string, string> = {}
      let performanceData: any = null
      let isComplete = false
      const completedModels = new Set<string>()

      function processStream() {
        reader!
          .read()
          .then(({ done, value }) => {
            if (done) {
              if (!isComplete) {
                resolve({
                  status: "success",
                  responses: modelTexts,
                  streaming: true,
                  performance_data: performanceData,
                })
              }
              return
            }

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split("\n")
            buffer = lines.pop() || ""

            for (const line of lines) {
              if (line.trim() === "") continue

              if (line.startsWith("data: ")) {
                const dataStr = line.slice(6).trim()

                if (dataStr === "[DONE]") {
                  isComplete = true
                  resolve({
                    status: "success",
                    responses: modelTexts,
                    streaming: true,
                    performance_data: performanceData,
                  })
                  return
                }

                try {
                  const data = JSON.parse(dataStr)
                  console.log("Streaming event:", data.event_type, data.model || data.model_name || "unknown")

                  switch (data.event_type) {
                    case "start":
                      console.log("Parallel analysis started with models:", data.models)
                      // Initialize all models with empty text
                      if (data.models && Array.isArray(data.models)) {
                        data.models.forEach((model: string) => {
                          modelTexts[model] = ""
                          modelStatus[model] = "starting"
                        })
                      }
                      break

                    case "model_start":
                      const modelName = data.model_name || data.model
                      if (modelName) {
                        if (!modelTexts[modelName]) {
                          modelTexts[modelName] = ""
                        }
                        modelStatus[modelName] = "active"
                        console.log(`Model ${modelName} started streaming`)

                        // Initialize UI with empty text for immediate streaming
                        if (onStreamUpdate) {
                          onStreamUpdate("", modelName)
                        }
                      }
                      break

                    case "text_generation":
                      const textModel = data.model || data.model_name
                      const textChunk = data.text || ""

                      if (textModel && textChunk) {
                        // Initialize if not exists
                        if (!modelTexts[textModel]) {
                          modelTexts[textModel] = ""
                        }

                        // Accumulate text chunk
                        modelTexts[textModel] += textChunk

                        console.log(
                          `Text chunk for ${textModel}: "${textChunk}" (total length: ${modelTexts[textModel].length})`,
                        )

                        // Update UI immediately with accumulated text
                        if (onStreamUpdate) {
                          onStreamUpdate(modelTexts[textModel], textModel, performanceData)
                        }
                      } else {
                        console.warn("Missing text or model in text_generation event:", {
                          textModel,
                          textChunk,
                          data,
                        })
                      }
                      break

                    case "model_end":
                      const endModel = data.model_name || data.model
                      if (endModel) {
                        modelStatus[endModel] = "completed"
                        completedModels.add(endModel)
                        responses[endModel] = modelTexts[endModel] || ""
                        console.log(
                          `Model ${endModel} completed with ${modelTexts[endModel]?.length || 0} characters`,
                        )

                        if (onStreamUpdate && modelTexts[endModel]) {
                          onStreamUpdate(modelTexts[endModel], endModel, performanceData)
                        }
                      }
                      break

                    case "complete":
                      // Copy all model texts to final responses
                      Object.assign(responses, modelTexts)
                      isComplete = true
                      console.log("Parallel streaming completed for all models")
                      console.log(
                        "Final responses:",
                        Object.keys(responses).map((model) => `${model}: ${responses[model]?.length || 0} chars`),
                      )
                      resolve({
                        status: "success",
                        responses: responses,
                        streaming: true,
                        performance_data: performanceData,
                      })
                      return

                    case "performance_data":
                      performanceData = data.data || data
                      break

                    case "performance_metrics":
                      // Store performance metrics for specific model
                      if (!performanceData) {
                        performanceData = {}
                      }
                      if (data.model && data.metrics) {
                        performanceData[data.model] = data.metrics
                        console.log(`Performance metrics for ${data.model}:`, data.metrics)
                        
                        // Call completion callback with performance data
                        if (onStreamComplete) {
                          onStreamComplete(data.model, data.metrics)
                        }
                      }
                      break

                    case "error":
                      const errorModel = data.model || "unknown"
                      const errorMessage = data.message || "Model failed"

                      if (errorModel !== "unknown") {
                        modelStatus[errorModel] = "error"
                        modelTexts[errorModel] = `Error: ${errorMessage}`
                        completedModels.add(errorModel)

                        if (onStreamUpdate) {
                          onStreamUpdate(modelTexts[errorModel], errorModel, performanceData)
                        }
                        console.log(`Model ${errorModel} failed: ${errorMessage}`)
                      } else {
                        console.error("General streaming error:", errorMessage)
                        reject(new Error(errorMessage))
                        return
                      }
                      break
                  }
                } catch (e) {
                  console.warn("Failed to parse parallel streaming data:", e, "Raw data:", dataStr)
                }
              }
            }

            processStream()
          })
          .catch(reject)
      }

      processStream()
    })
  }

  // API Key Management
  async disconnectApiKey() {
    return this.requestWithBaseUrl(NEXT_API_BASE_URL, "/disconnect", {
      method: "POST",
    })
  }

  async checkApiKeyStatus(): Promise<{ connected: boolean; type?: string; source?: string }> {
    return this.requestWithBaseUrl(NEXT_API_BASE_URL, "/status")
  }

  // Performance and Stats
  async getPerformanceStats(): Promise<PerformanceStats> {
    return this.request("/api/stats")
  }

  async getRecentComparisons(): Promise<any> {
    return this.request("/api/recent-comparisons")
  }

  async exportData(format: "json" | "csv" = "json"): Promise<any> {
    return this.request(`/api/export?format=${format}`)
  }

  // Cache Management
  async optimizeCache(): Promise<any> {
    return this.request("/api/optimize-cache", { method: "POST" })
  }

  async clearCache(): Promise<any> {
    return this.request("/api/clear-cache", { method: "POST" })
  }

  async getCacheStats(): Promise<any> {
    return this.request("/api/cache-stats")
  }

  // Video Processing
  async preloadFrames(indexId: string, videoId: string): Promise<any> {
    return this.request("/api/preload-frames", {
      method: "POST",
      body: JSON.stringify({ index_id: indexId, video_id: videoId }),
    })
  }

  async getVideoStatus(indexId: string, videoId: string): Promise<any> {
    return this.request(`/api/video-status/${indexId}/${videoId}`)
  }
}

export const apiService = new ApiService()
