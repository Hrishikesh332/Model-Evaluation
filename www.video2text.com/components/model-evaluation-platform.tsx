"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Loader2,
  Send,
  ExternalLink,
  Clock,
  Film,
  Settings,
  Star,
  Mic,
  Github,
  Sun,
  Moon,
  Trophy,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react"
import { apiService, type Index, type Video, type ModelStatus } from "@/lib/api"
import { useTheme } from "next-themes"
import { useApiState } from "@/hooks/use-api-state"

interface ModelResponse {
  id: string
  query: string
  response: string
  model: string
  timestamp: Date
  isLoading?: boolean
  error?: boolean
  isUser?: boolean
  performanceData?: any
  isStreaming?: boolean
}

const parseTimestamps = (text: string) => {
  // Instead of splitting text into parts, we'll render the text normally
  // and use a different approach to highlight timestamps inline
  return [{ type: "text", content: text }]
}

const ResponseContent = ({ response, performanceData, isStreaming = false }: { response: string; performanceData?: any; isStreaming?: boolean }) => {
  const parsedContent = parseTimestamps(response)

  const renderMarkdownText = (text: string) => {
    // Split by lines to handle numbered lists and headers
    const lines = text.split("\n")

    return lines.map((line, lineIndex) => {
      // Handle headers (## Header)
      if (/^#{1,6}\s/.test(line)) {
        const level = line.match(/^(#{1,6})\s/)?.[1].length || 1
        const content = line.replace(/^#{1,6}\s/, '')
        const className = level === 1 ? 'text-2xl font-bold' : 
                         level === 2 ? 'text-xl font-bold' : 
                         level === 3 ? 'text-lg font-semibold' : 
                         'text-base font-medium'
        return (
          <div key={lineIndex} className={`${className} text-foreground mb-2 mt-4`}>
            {content}
          </div>
        )
      }

      // Handle numbered lists (1. 2. 3. etc.) - ensure new line for each
      if (/^\d+\.\s/.test(line)) {
        const content = line.replace(/^\d+\.\s/, '')
        const number = line.match(/^(\d+)\.\s/)?.[1] || ''
        return (
          <div key={lineIndex} className="mb-3 pl-4 flex items-start">
            <span className="text-muted-foreground mr-3 mt-0.5 font-medium min-w-[20px] flex-shrink-0">{number}.</span>
            <div className="text-foreground flex-1 min-w-0">
              {renderInlineTimestamps(content)}
            </div>
          </div>
        )
      }

      // Handle sub-points within numbered sections (lines starting with - or *)
      if (/^\s*[-*]\s/.test(line)) {
        const content = line.replace(/^\s*[-*]\s/, '')
        return (
          <div key={lineIndex} className="mb-2 pl-8 flex items-start">
            <span className="text-muted-foreground mr-2 mt-0.5 flex-shrink-0">•</span>
            <div className="text-foreground flex-1 min-w-0">{renderInlineTimestamps(content)}</div>
          </div>
        )
      }

      // Handle bullet points with bold headers
      if (/^\s*-\s\*\*/.test(line)) {
        const parts = line.split("**")
        return (
          <div key={lineIndex} className="mb-2 pl-8 flex items-start">
            <span className="text-muted-foreground mr-2 mt-0.5 flex-shrink-0">•</span>
            <span className="font-medium text-foreground flex-shrink-0">{parts[1]}</span>
            {parts[2] && <span className="text-muted-foreground ml-1 flex-1 min-w-0">{renderInlineTimestamps(parts[2].replace(/^:\s*/, ""))}</span>}
          </div>
        )
      }

      // Handle regular bold text
      if (line.includes("**")) {
        const parts = line.split("**")
        return (
          <div key={lineIndex} className="mb-2">
            {parts.map((part, partIndex) => (
              <span key={partIndex} className={partIndex % 2 === 1 ? "font-semibold text-foreground" : "text-foreground"}>
                {renderInlineTimestamps(part)}
              </span>
            ))}
          </div>
        )
      }

      // Handle italic text
      if (line.includes("*") && !line.includes("**")) {
        const parts = line.split("*")
        return (
          <div key={lineIndex} className="mb-2">
            {parts.map((part, partIndex) => (
              <span key={partIndex} className={partIndex % 2 === 1 ? "italic text-foreground" : "text-foreground"}>
                {renderInlineTimestamps(part)}
              </span>
            ))}
          </div>
        )
      }

      // Handle code blocks
      if (line.startsWith("```")) {
        return (
          <div key={lineIndex} className="mb-2">
            <div className="bg-muted/50 p-3 rounded-md font-mono text-sm overflow-x-auto">
              {line.replace(/```/, '')}
            </div>
          </div>
        )
      }

      // Handle inline code
      if (line.includes("`")) {
        const parts = line.split("`")
        return (
          <div key={lineIndex} className="mb-2">
            {parts.map((part, partIndex) => (
              <span key={partIndex} className={partIndex % 2 === 1 ? "bg-muted/50 px-1 rounded font-mono text-sm" : "text-foreground"}>
                {renderInlineTimestamps(part)}
              </span>
            ))}
          </div>
        )
      }

      if (line.trim()) {
        return (
          <div key={lineIndex} className="mb-2">
            <span className="text-foreground leading-relaxed break-words">
              {renderInlineTimestamps(line)}
            </span>
          </div>
        )
      }

      return <div key={lineIndex} className="h-2"></div>
    })
  }

  // Function to render timestamps inline within text
  const renderInlineTimestamps = (text: string) => {
    const timestampRegex = /(\d{1,2}:\d{2})(?:[-,]\s*(\d{1,2}:\d{2}))?/g
    const parts = []
    let lastIndex = 0
    let match

    while ((match = timestampRegex.exec(text)) !== null) {
      // Add text before the timestamp
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index))
      }

      // Add the timestamp as a minimalistic light green button
      const timestampContent = match[2] ? `${match[1]} - ${match[2]}` : match[1]
      parts.push(
        <button
          key={`timestamp-${match.index}`}
          className="inline-flex items-center gap-1 px-2 py-1 mx-1 text-xs font-mono bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200 border border-green-300 dark:border-green-600/60 rounded-sm hover:bg-green-200 dark:hover:bg-green-900/30 transition-colors duration-200 flex-shrink-0"
        >
          <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="font-mono">{timestampContent}</span>
        </button>
      )

      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex))
    }

    return parts.length > 0 ? parts : text
  }

  // During streaming, show plain text to prevent layout shifts
  if (isStreaming) {
    console.log("ResponseContent: Rendering streaming view for response length:", response.length)
    return (
      <div className="space-y-2">
        <div className="prose prose-sm max-w-none overflow-hidden">
          <div className="text-foreground leading-relaxed break-words whitespace-pre-wrap font-mono text-sm bg-muted/30 p-3 rounded-md relative">
            <div className="absolute top-2 right-2 flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Streaming...</span>
            </div>
            {response}
          </div>
        </div>
      </div>
    )
  }

  // After streaming is complete, render the full markdown with timestamps
  console.log("ResponseContent: Rendering final markdown view for response length:", response.length)

  // After streaming is complete, render the full markdown with timestamps
  return (
    <div className="space-y-2 animate-in fade-in-0 slide-in-from-bottom-2 duration-500">
      <div className="prose prose-sm max-w-none overflow-hidden">
        {renderMarkdownText(response)}
      </div>

      {/* Only show performance metrics for model responses when streaming is complete and we have real data */}
      {performanceData && !response.includes("You") && performanceData.throughput && performanceData.duration && (
        <PerformanceMetrics metrics={performanceData} />
      )}
    </div>
  )
}

// Simple Loading Component
const LoadingResponse = ({ response, timestamp }: { response: string; timestamp: Date }) => {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Loader2 className="w-4 h-4 animate-spin" />
      <span>{response}</span>
    </div>
  )
}

// Performance Metrics Component
const PerformanceMetrics = ({ metrics }: { metrics: any }) => {
  console.log("PerformanceMetrics component called with:", metrics)
  
  // Only show if we have real performance data
  if (!metrics || !metrics.throughput || !metrics.duration) {
    console.log("No real performance data available")
    return null
  }

  console.log("Displaying real performance metrics:", metrics)

  return (
    <div className="mt-3 p-3 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/30 dark:to-teal-900/30 rounded-lg border border-emerald-200 dark:border-emerald-700 shadow-sm">
      <div className="flex items-center justify-between">
        {/* Left side - Rocket and metrics */}
        <div className="flex items-center gap-3">
          {/* Rocket Icon */}
          <div className="flex-shrink-0">
            <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          
          {/* Metrics */}
          <div className="flex items-center gap-4 text-xs">
            {/* Throughput */}
            <div className="flex items-center gap-1">
              <span className="font-bold text-emerald-700 dark:text-emerald-300 text-sm">
                {metrics.throughput}
              </span>
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">t/s</span>
            </div>
            
            {/* Duration with Clock Icon */}
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-bold text-emerald-700 dark:text-emerald-300 text-sm">
                {metrics.duration}s
              </span>
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">total duration</span>
            </div>
          </div>
        </div>

        {/* Right side - Additional info */}
        <div className="text-xs text-emerald-600 dark:text-emerald-400">
          {metrics.word_count && (
            <span className="mr-2">Words: {metrics.word_count}</span>
          )}
          {metrics.char_count && (
            <span>Chars: {metrics.char_count}</span>
          )}
        </div>
      </div>
    </div>
  )
}

export function ModelEvaluationPlatform() {
  const [selectedIndex, setSelectedIndex] = useState<Index | null>(null)
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)
  const [indexes, setIndexes] = useState<Index[]>([])
  const [videos, setVideos] = useState<Video[]>([])
  const [availableModels, setAvailableModels] = useState<ModelStatus | null>(null)
  const [apiKey, setApiKey] = useState("")
  const [message, setMessage] = useState("")
  const [leftModel, setLeftModel] = useState("gemini")
  const [rightModel, setRightModel] = useState("pegasus")
  const [leftResponses, setLeftResponses] = useState<ModelResponse[]>([])
  const [rightResponses, setRightResponses] = useState<ModelResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingData, setIsLoadingData] = useState(false)
  const [alert, setAlert] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false)
  const [currentTutorialStep, setCurrentTutorialStep] = useState(0)
  const { theme, setTheme } = useTheme()
  const [isVideoProcessing, setIsVideoProcessing] = useState(false)
  const [videoProcessingStatus, setVideoProcessingStatus] = useState<string>("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [performanceData, setPerformanceData] = useState<any>(null)
  const [leftStreamingStarted, setLeftStreamingStarted] = useState(false)
  const [rightStreamingStarted, setRightStreamingStarted] = useState(false)
  
  // Use the custom hook for API state management
  const {
    isConnected,
    apiMode,
    isApiConnected,
    isLoading: isApiLoading,
    error: apiError,
    checkApiStatus,
    connectApiKey: hookConnectApiKey,
    disconnectApiKey: hookDisconnectApiKey
  } = useApiState()

  // Tutorial steps data
  const tutorialSteps = [
    {
      title: "Welcome to Model Evaluation Platform",
      description:
        "Search, Analyze, and Embed are now available directly within your index. Explore all your features right where your videos live!",
      image: "/placeholder.svg?height=300&width=500",
    },
    {
      title: "Connect Your API Key",
      description:
        "Connect your TwelveLabs API key to access your personal indexes and videos for comprehensive analysis.",
      image: "/placeholder.svg?height=300&width=500",
    },
    {
      title: "Select Your Content",
      description:
        "Choose from your video indexes and select specific videos to analyze with multiple AI models simultaneously.",
      image: "/placeholder.svg?height=300&width=500",
    },
    {
      title: "Compare AI Models",
      description:
        "Get insights from different AI models side-by-side and compare their analysis capabilities in real-time.",
      image: "/placeholder.svg?height=300&width=500",
    },
  ]

  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoadingData(true)
      try {
        // Load indexes
        const indexesResponse = await apiService.getIndexes()
        setIndexes(indexesResponse.indexes)
        
        if (indexesResponse.indexes.length > 0) {
          setSelectedIndex(indexesResponse.indexes[0])
        }

        // Load available models
        const modelsResponse = await apiService.getModels()
        setAvailableModels(modelsResponse.models)

        if (modelsResponse.models["gemini-2.0-flash"]) setLeftModel("gemini-2.0-flash")
        else if (modelsResponse.models["gemini-2.5-pro"]) setLeftModel("gemini-2.5-pro")
        else if (modelsResponse.models.nova) setLeftModel("nova")

        if (modelsResponse.models["pegasus-1.2"]) setRightModel("pegasus-1.2")
        else if (modelsResponse.models.nova) setRightModel("nova")

        const statusMessage = apiMode === "user" 
          ? "Connected using user API key" 
          : "Connected using environment API configuration"
        showAlert(statusMessage, "success")
      } catch (error) {
        console.error("Failed to load initial data:", error)
        showAlert("Failed to connect to API. Please check your connection and try again.", "error")
      } finally {
        setIsLoadingData(false)
      }
    }

    // Only load data when API state is ready
    if (!isApiLoading) {
      loadInitialData()
    }
  }, [isApiLoading, apiMode])

  useEffect(() => {
    const loadVideos = async () => {
      if (selectedIndex) {
        setIsLoadingData(true)
        console.log(`Loading videos for index: ${selectedIndex.name} (${selectedIndex.id})`)
        try {
          const videosResponse = await apiService.getVideos(selectedIndex.id)
          console.log(`Loaded ${videosResponse.videos.length} videos for index ${selectedIndex.name}`)
          setVideos(videosResponse.videos)

          if (videosResponse.videos.length > 0) {
            setSelectedVideo(videosResponse.videos[0])
            // Select the video in the API
            await apiService.selectVideo(selectedIndex.id, videosResponse.videos[0].id)
            console.log(`Auto-selected first video: ${videosResponse.videos[0].name}`)
          } else {
            // Handle case where index has no videos
            setSelectedVideo(null)
            showAlert(`Warning: The index "${selectedIndex.name}" has no videos. Please add videos to this index or select a different index.`, "info")
          }
        } catch (error) {
          console.error("Failed to load videos:", error)
          
          // Check if it's a 404 error (no videos in index)
          if (error instanceof Error && error.message.includes('404')) {
            setVideos([])
            setSelectedVideo(null)
            showAlert(`Warning: The index "${selectedIndex.name}" has no videos. Please add videos to this index or select a different index.`, "info")
          } else {
            showAlert("Failed to load videos. Please try again.", "error")
            setVideos([])
          }
        } finally {
          setIsLoadingData(false)
        }
      } else {
        setVideos([])
        setSelectedVideo(null)
      }
    }

    loadVideos()
  }, [selectedIndex, isConnected])



  const showAlert = (message: string, type: "success" | "error" | "info") => {
    setAlert({ message, type })
    setTimeout(() => setAlert(null), 5000)
  }

  const handleApiConnect = async () => {
    if (!apiKey.trim()) {
      showAlert("Please enter a valid API key", "error")
      return
    }

    setIsConnecting(true)
    showAlert("Connecting to TwelveLabs API...", "info")

    try {
      // Step 1: Connect the API key
      console.log("Step 1: Connecting API key...")
      await hookConnectApiKey("twelvelabs", apiKey)

      // Step 2: Clear existing data immediately
      console.log("[v0] Step 2: Clearing existing data...")
      setIndexes([])
      setVideos([])
      setSelectedIndex(null)
      setSelectedVideo(null)
      setLeftResponses([])
      setRightResponses([])

      // Step 3: Wait for session to be established
      console.log("[v0] Step 3: Waiting for session establishment...")
      await new Promise((resolve) => setTimeout(resolve, 2000))

      // Step 4: Validate API key is working by fetching user's data
      console.log("[v0] Step 4: Validating API key and fetching user data...")
      setIsLoadingData(true)

      let retryCount = 0
      const maxRetries = 3
      let indexesResponse = null

      // Retry mechanism to ensure we get user's data
      while (retryCount < maxRetries && !indexesResponse) {
        try {
          console.log(`[v0] Attempt ${retryCount + 1}: Fetching user's indexes...`)
          indexesResponse = await apiService.getIndexes()

          console.log("[v0] Raw indexes response:", indexesResponse)

          // Handle both direct array and wrapped response formats
          let indexesArray = null
          if (Array.isArray(indexesResponse)) {
            indexesArray = indexesResponse
          } else if (indexesResponse && Array.isArray(indexesResponse.indexes)) {
            indexesArray = indexesResponse.indexes
          } else if (indexesResponse && Array.isArray(indexesResponse.data)) {
            indexesArray = indexesResponse.data
          }

          if (indexesArray && indexesArray.length >= 0) {
            console.log(`[v0] Success! Found ${indexesArray.length} indexes for user`)
            indexesResponse = { indexes: indexesArray }
            break
          } else {
            throw new Error("No valid indexes data received")
          }
        } catch (error) {
          retryCount++
          console.error(`[v0] Attempt ${retryCount} failed:`, error)
          if (retryCount < maxRetries) {
            console.log(`[v0] Retrying in ${retryCount * 1000}ms...`)
            await new Promise((resolve) => setTimeout(resolve, retryCount * 1000))
          }
        }
      }

      if (!indexesResponse || !indexesResponse.indexes) {
        throw new Error("Failed to fetch user's indexes after multiple attempts. Please check your API key.")
      }

      // Step 5: Update state with user's data
      console.log("[v0] Step 5: Updating UI with user's data...")
      console.log("[v0] Setting indexes to:", indexesResponse.indexes)
      setIndexes(indexesResponse.indexes)

      await new Promise((resolve) => setTimeout(resolve, 100))

      // Step 6: Auto-select first index and load its videos
      if (indexesResponse.indexes.length > 0) {
        const firstIndex = indexesResponse.indexes[0]
        console.log("[v0] Auto-selecting first index:", firstIndex)
        setSelectedIndex(firstIndex)

        console.log("[v0] Step 6: Loading videos for first index...")
        try {
          const videosResponse = await apiService.getVideos(firstIndex.id)
          console.log("[v0] Videos response:", videosResponse)

          let videosArray = null
          if (Array.isArray(videosResponse)) {
            videosArray = videosResponse
          } else if (videosResponse && Array.isArray(videosResponse.videos)) {
            videosArray = videosResponse.videos
          } else if (videosResponse && Array.isArray(videosResponse.data)) {
            videosArray = videosResponse.data
          }

          if (videosArray) {
            console.log(`[v0] Loaded ${videosArray.length} videos for index ${firstIndex.name}`)
            setVideos(videosArray)

            if (videosArray.length > 0) {
              const firstVideo = videosArray[0]
              setSelectedVideo(firstVideo)
              console.log(`[v0] Auto-selected video: ${firstVideo.name}`)

              try {
                await apiService.selectVideo(firstIndex.id, firstVideo.id)
                console.log("[v0] Video selected in backend for analysis")
              } catch (selectError) {
                console.warn("[v0] Failed to select video in backend:", selectError)
                // Continue anyway - this is not critical for the connection
              }

              showAlert(
                `✅ Successfully connected! Loaded ${indexesResponse.indexes.length} indexes and ${videosArray.length} videos from your TwelveLabs account.`,
                "success",
              )
            } else {
              showAlert(
                `✅ Connected to TwelveLabs API. Found ${indexesResponse.indexes.length} indexes but no videos in the selected index.`,
                "info",
              )
            }
          } else {
            throw new Error("Invalid videos response format")
          }
        } catch (error) {
          console.error("[v0] Failed to load videos after API connection:", error)
          showAlert(
            `✅ Connected to TwelveLabs API with ${indexesResponse.indexes.length} indexes, but failed to load videos. Please try selecting an index manually.`,
            "info",
          )
        }
      } else {
        showAlert(
          "✅ Connected to TwelveLabs API, but no indexes found in your account. Please create an index first.",
          "info",
        )
      }

      setIsDialogOpen(false)
      setApiKey("")
    } catch (error) {
      console.error("[v0] API connection failed:", error)
      showAlert(
        `❌ Failed to connect: ${error instanceof Error ? error.message : "Unknown error"}. Please check your API key.`,
        "error",
      )
    } finally {
      setIsConnecting(false)
      setIsLoadingData(false)
    }
  }

  const handleSwitchToDefault = async () => {
    try {
      setIsConnecting(true)
      showAlert("Switching to default API configuration...", "info")
      
      await hookDisconnectApiKey()
      setApiKey("")

      // Clear responses and reload data
      setLeftResponses([])
      setRightResponses([])
      setIndexes([])
      setVideos([])
      setSelectedIndex(null)
      setSelectedVideo(null)

      showAlert("✅ Switched to default API configuration. Reloading data...", "success")

      setIsDialogOpen(false)
      
      // Wait a moment for the disconnect to complete, then reload data
      setTimeout(async () => {
        try {
          setIsLoadingData(true)
          const indexesResponse = await apiService.getIndexes()
          setIndexes(indexesResponse.indexes)
          
          if (indexesResponse.indexes.length > 0) {
            setSelectedIndex(indexesResponse.indexes[0])
          }
          
          showAlert("✅ Default configuration loaded successfully", "success")
        } catch (error) {
          console.error("Failed to reload data with default config:", error)
          showAlert("⚠️ Switched to default but failed to reload data. Please refresh the page.", "info")
        } finally {
          setIsLoadingData(false)
          setIsConnecting(false)
        }
      }, 1000)
    } catch (error) {
      console.error("Failed to disconnect API key:", error)
      showAlert("Failed to disconnect API key. Please try again.", "error")
      setIsConnecting(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    if (!selectedVideo) {
      showAlert("Please select a video first", "error")
      return
    }
    setMessage(suggestion)
  }

  const handleVideoSelect = async (videoId: string) => {
    const video = videos.find((v) => v.id === videoId)
    if (video && selectedIndex) {
      setSelectedVideo(video)
      setLeftResponses([])
      setRightResponses([])
      setIsVideoProcessing(true)
      setVideoProcessingStatus("Processing video frames...")

      try {
        await apiService.selectVideo(selectedIndex.id, video.id)
        setTimeout(() => {
          setIsVideoProcessing(false)
          setVideoProcessingStatus("Video ready for analysis")
          showAlert(`Video processed and ready: ${video.name}`, "success")
        }, 2000)
      } catch (error) {
        console.error("Failed to select video:", error)
        setIsVideoProcessing(false)
        setVideoProcessingStatus("")
        showAlert("Failed to select video. Please try again.", "error")
      }
    }
  }

  const handleStreamUpdate = (fullText: string, modelName: string, performanceData?: any) => {
    const currentTimestamp = new Date()

    console.log(`[v0] handleStreamUpdate called - Model: ${modelName}, Text length: ${fullText.length}`)
    console.log(`[v0] Performance data received:`, performanceData)

    // Helper function to stop loading after a brief delay to ensure UI updates
    const stopLoadingWithDelay = (isLeft: boolean) => {
      setTimeout(() => {
        if (isLeft) {
          setLeftResponses((prev) => {
            const newResponses = [...prev]
            const lastIndex = newResponses.length - 1
            if (newResponses[lastIndex] && newResponses[lastIndex].isLoading) {
              newResponses[lastIndex] = {
                ...newResponses[lastIndex],
                isLoading: false,
              }
            }
            return newResponses
          })
        } else {
          setRightResponses((prev) => {
            const newResponses = [...prev]
            const lastIndex = newResponses.length - 1
            if (newResponses[lastIndex] && newResponses[lastIndex].isLoading) {
              newResponses[lastIndex] = {
                ...newResponses[lastIndex],
                isLoading: false,
              }
            }
            return newResponses
          })
        }
      }, 1000) // 1 second delay to ensure loader is visible
    }

    // Update left compartment if it matches the left model
    if (modelName === leftModel) {
      console.log(`[v0] Updating left compartment for ${modelName}`)
      setLeftStreamingStarted(true)
      setLeftResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && !newResponses[lastIndex]?.error) {
          newResponses[lastIndex] = {
            ...newResponses[lastIndex],
            response: fullText,
            model: leftModel,
            timestamp: currentTimestamp,
            isLoading: true, // Keep loading for a moment
            isStreaming: true,
            performanceData: performanceData,
          }
          console.log(`[v0] Left compartment updated with ${fullText.length} characters and performance data:`, performanceData)
          
              // Stop loading after delay
    stopLoadingWithDelay(true)
    
    // Also mark streaming as complete after a longer delay as fallback
    setTimeout(() => {
      setLeftResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && newResponses[lastIndex].isStreaming) {
          newResponses[lastIndex] = {
            ...newResponses[lastIndex],
            isStreaming: false,
          }
          console.log(`[v0] Fallback: Left compartment streaming marked as complete`)
        }
        return newResponses
      })
    }, 3000) // 3 second fallback
        }
        return newResponses
      })
    }

    // Update right compartment if it matches the right model
    if (modelName === rightModel) {
      console.log(`[v0] Updating right compartment for ${modelName}`)
      setRightStreamingStarted(true)
      setRightResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && !newResponses[lastIndex]?.error) {
          newResponses[lastIndex] = {
            ...newResponses[lastIndex],
            response: fullText,
            model: rightModel,
            timestamp: currentTimestamp,
            isLoading: true, // Keep loading for a moment
            isStreaming: true,
            performanceData: performanceData,
          }
          console.log(`[v0] Right compartment updated with ${fullText.length} characters and performance data:`, performanceData)
          
          // Stop loading after delay
          stopLoadingWithDelay(false)
        }
        return newResponses
      })
    }

    // Handle case where model doesn't match left/right selection - assign to available compartment
    if (modelName !== leftModel && modelName !== rightModel) {
      console.log(`[v0] Model ${modelName} doesn't match selected models, assigning to right compartment`)
      setRightStreamingStarted(true)
      setRightResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && !newResponses[lastIndex]?.error) {
          newResponses[lastIndex] = {
            ...newResponses[lastIndex],
            response: fullText,
            model: modelName,
            timestamp: currentTimestamp,
            isLoading: true, // Keep loading for a moment
            isStreaming: true,
            performanceData: performanceData,
          }
          
          // Stop loading after delay
          stopLoadingWithDelay(false)
          
          // Also mark streaming as complete after a longer delay as fallback
          setTimeout(() => {
            setRightResponses((prev) => {
              const newResponses = [...prev]
              const lastIndex = newResponses.length - 1
              if (newResponses[lastIndex] && newResponses[lastIndex].isStreaming) {
                newResponses[lastIndex] = {
                  ...newResponses[lastIndex],
                  isStreaming: false,
                }
                console.log(`[v0] Fallback: Right compartment streaming marked as complete for ${modelName}`)
              }
              return newResponses
            })
          }, 3000) // 3 second fallback
        }
        return newResponses
      })
    }
  }

  const handleStreamComplete = (modelName: string, finalPerformanceData?: any) => {
    console.log(`[v0] handleStreamComplete called - Model: ${modelName}, Final performance data:`, finalPerformanceData)
    console.log(`[v0] Current left model: ${leftModel}, right model: ${rightModel}`)
    
    const currentTimestamp = new Date()

    // Update left compartment if it matches the left model
    if (modelName === leftModel) {
      setLeftResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && !newResponses[lastIndex]?.error) {
          newResponses[lastIndex] = {
            ...newResponses[lastIndex],
            model: leftModel,
            timestamp: currentTimestamp,
            isLoading: false,
            isStreaming: false, // Mark streaming as complete
            performanceData: finalPerformanceData || newResponses[lastIndex].performanceData,
          }
          console.log(`[v0] Left compartment streaming completed for ${modelName}`)
        }
        return newResponses
      })
    }

    // Update right compartment if it matches the right model
    if (modelName === rightModel) {
      setRightResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && !newResponses[lastIndex]?.error) {
          newResponses[lastIndex] = {
            ...newResponses[lastIndex],
            model: rightModel,
            timestamp: currentTimestamp,
            isLoading: false,
            isStreaming: false, // Mark streaming as complete
            performanceData: finalPerformanceData || newResponses[lastIndex].performanceData,
          }
          console.log(`[v0] Right compartment streaming completed for ${modelName}`)
        }
        return newResponses
      })
    }

    // Handle case where model doesn't match left/right selection - assign to available compartment
    if (modelName !== leftModel && modelName !== rightModel) {
      console.log(`[v0] Model ${modelName} doesn't match selected models, completing in right compartment`)
      setRightResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && !newResponses[lastIndex]?.error) {
          newResponses[lastIndex] = {
            ...newResponses[lastIndex],
            model: modelName,
            timestamp: currentTimestamp,
            isLoading: false,
            isStreaming: false, // Mark streaming as complete
            performanceData: finalPerformanceData || newResponses[lastIndex].performanceData,
          }
          console.log(`[v0] Right compartment streaming completed for ${modelName}`)
        }
        return newResponses
      })
    }

    // Separator will be shown automatically by the useEffect when streaming completes
    console.log("[v0] Streaming completed, separator should be visible")
  }

  const handleSendMessage = async () => {
    if (!message.trim() || isVideoProcessing) return

    const currentTimestamp = new Date()
    const userMessage = message.trim()
    
    // Reset streaming states for new query
    setLeftStreamingStarted(false)
    setRightStreamingStarted(false)

    // Clear input
    setMessage("")

    // Clear previous responses to make it feel fresh
    setLeftResponses([])
    setRightResponses([])

    // Add user message to both compartments
    const userResponse = {
      response: userMessage,
      model: "user",
      timestamp: currentTimestamp,
      isLoading: false,
      isUser: true,
      error: null,
      isStreaming: false,
      performanceData: null,
    }

    // Add user message to both compartments simultaneously
    setLeftResponses([userResponse])
    setRightResponses([userResponse])
    setLastUserQueryIndex(0)

    // Synchronize scroll positions after adding user query
    setTimeout(() => {
      const leftPanel = document.querySelector('.left-panel .overflow-y-auto') as HTMLElement
      const rightPanel = document.querySelector('.right-panel .overflow-y-auto') as HTMLElement
      
      if (leftPanel && rightPanel) {
        // Scroll both panels to the bottom to show the new user query
        leftPanel.scrollTop = leftPanel.scrollHeight
        rightPanel.scrollTop = rightPanel.scrollHeight
      }
    }, 50)

    // Add loading responses for both models
    const leftLoadingResponse = {
      response: "Loading...",
      model: leftModel,
      timestamp: currentTimestamp,
      isLoading: true,
      isUser: false,
      error: null,
      isStreaming: false,
      performanceData: null,
    }

    const rightLoadingResponse = {
      response: "Loading...",
      model: rightModel,
      timestamp: currentTimestamp,
      isLoading: true,
      isUser: false,
      error: null,
      isStreaming: false,
      performanceData: null,
    }

    setLeftResponses((prev) => [...prev, leftLoadingResponse])
    setRightResponses((prev) => [...prev, rightLoadingResponse])

    // Add a small delay to make the loading state feel more natural
    await new Promise(resolve => setTimeout(resolve, 100))

    try {
      console.log(`[v0] Starting parallel analysis with models: ${leftModel} and ${rightModel}`)
      
      const result = await apiService.analyzeVideoParallel(
        userMessage,
        [leftModel, rightModel],
        "parallel",
        true,
        selectedIndex?.id, // Use selectedIndex.id for index_id
        selectedVideo.id, // Use selectedVideo.id for video_id
        handleStreamUpdate, // Handle streaming updates
        handleStreamComplete, // Handle streaming completion
      )

      console.log("[v0] Parallel analysis completed:", result)
    } catch (error) {
      console.error("[v0] Error in parallel analysis:", error)
      
      // Check if this is a video access denied error
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred"
      if (errorMessage.includes("Video access denied") || errorMessage.includes("not authorized")) {
        showAlert(
          "🚫 Video Access Denied: This video belongs to a different account. Please select a video from your own account or switch back to default mode.",
          "error"
        )
        
        // Clear the current selection to force user to select a new video
        setSelectedVideo(null)
        setVideos([])
      } else {
        showAlert(`❌ Analysis failed: ${errorMessage}`, "error")
      }
      
      // Handle errors for both compartments
      const errorResponse = {
        response: `Error: ${errorMessage}`,
        model: "error",
        timestamp: new Date(),
        isLoading: false,
        isUser: false,
        error: true,
        isStreaming: false,
        performanceData: null,
      }

      setLeftResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && newResponses[lastIndex].isLoading) {
          newResponses[lastIndex] = errorResponse
        }
        return newResponses
      })

      setRightResponses((prev) => {
        const newResponses = [...prev]
        const lastIndex = newResponses.length - 1
        if (newResponses[lastIndex] && newResponses[lastIndex].isLoading) {
          newResponses[lastIndex] = errorResponse
        }
        return newResponses
      })
    }
  }

  const handleNextTutorial = () => {
    setCurrentTutorialStep((prev) => (prev + 1) % tutorialSteps.length)
  }

  const handlePreviousTutorial = () => {
    setCurrentTutorialStep((prev) => (prev - 1 + tutorialSteps.length) % tutorialSteps.length)
  }

  const leftSuggestions = [
    "Provide a scene by scene breakdown of this video",
    "Compare the beginning and ending segments of this video",
    "Explain standout performance moments",
  ]

  const rightSuggestions = [
    "Do provide the key moments captured in Video",
    "Explain the main topic or theme of the video?",
    "Provide the genre and purpose of video",
  ]

  const getAvailableLeftModels = () => {
    if (!availableModels) return []
    const models = []
    if (availableModels["gemini-2.0-flash"])
      models.push({ value: "gemini-2.0-flash", label: "Gemini 2.0 Flash", provider: "Google" })
    if (availableModels["gemini-2.5-pro"])
      models.push({ value: "gemini-2.5-pro", label: "Gemini 2.5 Pro", provider: "Google" })
    if (availableModels.gpt4o) models.push({ value: "gpt4o", label: "GPT-4o", provider: "OpenAI" })
    if (availableModels.nova) models.push({ value: "nova", label: "AWS Nova", provider: "Amazon" })
    return models
  }

  const getAvailableRightModels = () => {
    if (!availableModels) return []
    const models = []
    if (availableModels["pegasus-1.2"])
      models.push({ value: "pegasus-1.2", label: "Pegasus 1.2", provider: "TwelveLabs" })
    if (availableModels.nova)
      models.push({ value: "nova", label: "AWS Nova", provider: "Amazon" })
    return models
  }

  // Track user query index for synchronization
  const [lastUserQueryIndex, setLastUserQueryIndex] = useState(-1)

  // Synchronize scroll positions between compartments
  useEffect(() => {
    const leftPanel = document.querySelector('.left-panel .overflow-y-auto') as HTMLElement
    const rightPanel = document.querySelector('.right-panel .overflow-y-auto') as HTMLElement
    
    if (leftPanel && rightPanel) {
      // Ensure both panels scroll to the bottom when new responses are added
      const scrollToBottom = () => {
        leftPanel.scrollTop = leftPanel.scrollHeight
        rightPanel.scrollTop = rightPanel.scrollHeight
      }
      
      // Scroll after a short delay to ensure content is rendered
      const timeoutId = setTimeout(scrollToBottom, 100)
      
      return () => clearTimeout(timeoutId)
    }
  }, [leftResponses.length, rightResponses.length, lastUserQueryIndex])

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top Navigation */}
      <header className="border-b bg-card/50 backdrop-blur-sm px-6 py-3 flex items-center justify-between sticky top-0 z-50 shadow-sm">
        <div className="flex items-center gap-4">
          {/* Logo */}
          <div className="logo-container">
            <svg id="Layer_1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 204 146.6" width="40px" height="40px">
              <defs>
                <style>
                  {`.st0 {
                    fill: hsl(var(--foreground));
                  }
                  .dark .st0 {
                    fill: white;
                  }`}
                </style>
              </defs>
              <rect className="st0" x="43.9" y="50.3" width="64.3" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" y="50.3" width="35.3" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="124.1" y="50.3" width="40.3" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="129.9" y="37.8" width="34.5" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="168.9" y="37.8" width="27.3" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="157.3" y="25" width="31.1" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="167.1" y="12.5" width="9.2" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="74.3" y="112.6" width="15.9" height="9" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="101.8" y="112.6" width="10.4" height="9" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="117" y="112.6" width="28" height="9" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="131" y="100.1" width="11.6" height="9" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="52.4" y="112.6" width="9.2" height="9" rx="2.6" ry="2.6"></rect>
              <path
                className="st0"
                d="M94.7,127.7c0-1.4,1.1-2.6,2.6-2.6h4c1.4,0,2.6,1.1-2.6,2.6v3.9c0,1.4-1.1,2.6-2.6,2.6h-4c-1.4,0-
2.6-1.1-2.6-2.6v-3c0-1.4,1.1-2.6,2.6-2.6h4c1.4,0,2.6,1.1-2.6,2.6v3.9c0,1.4-1.1,2.6-2.6,2.6h-4c-1.4,0-2.6-1.1-2.6-2.6v-3.9Z"
              ></path>
              <rect className="st0" x="85.8" y="137.6" width="8.7" height="9" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="120.4" width="11.4" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="55.8" y="37.8" width="29" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="109.7" y="12.5" width="17.6" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="98.8" y="25" width="28.5" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="187.4" y="50.3" width="16.6" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="30.6" y="62.8" width="82.1" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="105.1" y="87.8" width="32.1" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="43.9" y="75.3" width="104.3" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="27.9" y="87.8" width="38.8" height="8.7" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="63.3" y="100.1" width="12.7" height="9" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="108.1" y="100.1" width="13.7" height="9" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="39.8" y="100.1" width="12.9" height="9" rx="2.6" ry="2.6"></rect>
              <rect className="st0" x="124.1" y="62.8" width="33.1" height="8.7" rx="2.6" ry="2.6"></rect>
            </svg>
          </div>

          <Badge
            variant="outline"
            className={`${
              apiMode === "user"
                ? "text-blue-600 border-blue-300 bg-blue-50 dark:text-blue-400 dark:border-blue-600 dark:bg-blue-950/30"
                : "text-green-600 border-green-300 bg-green-50 dark:text-green-400 dark:border-green-600 dark:bg-green-950/30"
            }`}
          >
            {apiMode === "user" ? "User API Mode" : "Default API Mode"}
          </Badge>

          {/* Index Selector */}
          <div className="flex items-center gap-2">
            <Select
              value={selectedIndex?.id}
              onValueChange={(value) => {
                const index = indexes.find((i) => i.id === value)
                setSelectedIndex(index || null)
                setLeftResponses([])
                setRightResponses([])
              }}
              disabled={isLoadingData}
            >
              <SelectTrigger className="w-48 bg-card border-border hover:bg-accent hover:text-accent-foreground transition-colors shadow-sm">
                <SelectValue
                  placeholder={
                    isLoadingData ? "Loading..." : indexes.length === 0 ? "No indexes available" : "Select Index"
                  }
                />
              </SelectTrigger>
              <SelectContent className="bg-card border-border shadow-lg">
                {indexes.map((index) => (
                  <SelectItem key={index.id} value={index.id} className="hover:bg-accent hover:text-accent-foreground">
                    <div className="flex items-center justify-between w-full">
                      <span>{index.name}</span>
                      <Badge 
                        variant={index.video_count === 0 ? "destructive" : "secondary"} 
                        className="ml-2 text-xs"
                      >
                        {index.video_count === 0 ? "No videos" : `${index.video_count} videos`}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {selectedIndex && (
              <Button variant="ghost" size="sm" className="hover:bg-accent hover:text-accent-foreground">
                <ExternalLink className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Video Selector */}
          <Select
            value={selectedVideo?.id}
            onValueChange={handleVideoSelect}
            disabled={!selectedIndex || videos.length === 0 || isLoadingData}
          >
            <SelectTrigger
              className={`w-64 transition-colors shadow-sm ${
                !selectedIndex || videos.length === 0 || isLoadingData
                  ? "bg-muted text-muted-foreground cursor-not-allowed border-muted"
                  : "bg-card border-border hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              <SelectValue
                placeholder={
                  isLoadingData
                    ? "Loading videos..."
                    : !selectedIndex
                      ? "Select an index first"
                      : videos.length === 0
                        ? "No videos in this index"
                        : "Select a video"
                }
              />
            </SelectTrigger>
            <SelectContent className="bg-card border-border shadow-lg">
              {videos.map((video) => (
                <SelectItem key={video.id} value={video.id} className="hover:bg-accent hover:text-accent-foreground">
                  <div className="flex items-center gap-3 w-full">
                    {/* Thumbnail */}
                    <div className="flex-shrink-0 w-12 h-8 rounded overflow-hidden bg-muted">
                      {video.thumbnailUrl ? (
                        <img
                          src={video.thumbnailUrl}
                          alt={`${video.name} thumbnail`}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            // Fallback to icon if thumbnail fails to load
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const parent = target.parentElement;
                            if (parent) {
                              parent.innerHTML = '<div class="w-full h-full flex items-center justify-center"><svg class="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg></div>';
                            }
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Film className="w-4 h-4 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                    
                    {/* Video Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="truncate font-medium">{video.name}</span>
                        <span className="text-xs text-muted-foreground whitespace-nowrap">({video.duration}s)</span>
                      </div>
                    </div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Right Section with About, leaderboard, GitHub, and theme toggle */}
        <div className="flex items-center gap-2">
          {/* About Logo */}
          <Dialog open={isAboutModalOpen} onOpenChange={setIsAboutModalOpen}>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                size="default"
                className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground px-3 py-2"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl w-[95vw] max-h-[85vh] border-0 p-6 bg-gradient-to-br from-green-400 via-yellow-300 to-pink-400 overflow-hidden">
              {/* Background image overlay */}
              <div
                className="absolute inset-0 opacity-80"
                style={{
                  backgroundImage: `url(https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Model%20Card%20from%20DevCircle-VjxitbETGDj9ZfTwq2KQVOlodag0TK.png)`,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                }}
              />

              <DialogClose asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute top-4 right-4 z-30 w-10 h-10 rounded-full bg-black/20 backdrop-blur-md border-2 border-white/30 hover:bg-black/40 hover:border-white/50 transition-all duration-200 text-white hover:text-white shadow-lg"
                >
                  <X className="w-5 h-5" />
                </Button>
              </DialogClose>

              {/* Content container with better visibility */}
              <div className="relative z-20 bg-black/40 backdrop-blur-md rounded-2xl p-8 h-full overflow-y-auto flex flex-col border border-white/20">
                <div className="text-center mb-8">
                  <h2 className="text-4xl font-bold text-white mb-4 drop-shadow-2xl">
                    Welcome to Model Evaluation Platform
                  </h2>
                  <p className="text-white text-lg leading-relaxed drop-shadow-lg font-medium">
                    {tutorialSteps[currentTutorialStep].description}
                  </p>
                </div>

                {/* Tutorial content with image */}
                <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 mb-8 border border-white/50 flex-shrink-0">
                  <img
                    src="/placeholder.svg?height=300&width=600"
                    alt={`Tutorial step ${currentTutorialStep + 1}`}
                    className="w-full h-48 object-cover rounded-lg shadow-xl"
                  />
                </div>

                {/* Navigation and step indicators */}
                <div className="flex items-center justify-between mt-auto">
                  <div className="flex space-x-3">
                    {tutorialSteps.map((_, index) => (
                      <div
                        key={index}
                        className={`w-4 h-4 rounded-full transition-all duration-300 border-2 ${
                          index === currentTutorialStep
                            ? "bg-white border-white shadow-lg scale-110"
                            : "bg-transparent border-white/60 hover:border-white hover:bg-white/20"
                        }`}
                      />
                    ))}
                  </div>

                  <div className="flex gap-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handlePreviousTutorial}
                      disabled={currentTutorialStep === 0}
                      className="text-white hover:bg-white/30 disabled:opacity-50 backdrop-blur-sm border-2 border-white/40 font-semibold"
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Previous
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleNextTutorial}
                      disabled={currentTutorialStep === tutorialSteps.length - 1}
                      className="text-white hover:bg-white/30 disabled:opacity-50 backdrop-blur-sm border-2 border-white/40 font-semibold"
                    >
                      Next
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* Leaderboard Logo */}
          <Button
            variant="ghost"
            size="sm"
            className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground"
            onClick={() =>
              showAlert("Leaderboard feature coming soon! Stay tuned for model performance rankings.", "info")
            }
          >
            <Trophy className="w-4 h-4" />
          </Button>

          {/* GitHub Logo */}
          <Button
            variant="ghost"
            size="sm"
            className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground"
            onClick={() => window.open("https://github.com/Hrishikesh332/Model-Evaluation", "_blank")}
          >
            <Github className="w-4 h-4" />
          </Button>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </Button>

          {/* API Connection Dialog */}
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 text-black dark:text-white">
                <Settings className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {isApiConnected ? "User API" : "Default API"}
                </span>
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-white dark:bg-black border-gray-200 dark:border-gray-800 max-w-md">
              <DialogHeader className="pb-4">
                <DialogTitle className="text-black dark:text-white text-lg font-medium">API Configuration</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-6">
                {/* Current Status */}
                <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
                  <div className={`w-3 h-3 rounded-full ${apiMode === "user" ? "bg-black dark:bg-white" : "bg-gray-400 dark:bg-gray-600"}`}></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-black dark:text-white">
                      {apiMode === "user" ? "User API Mode" : "Default Mode"}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {apiMode === "user" 
                        ? "Using your personal API key" 
                        : "Using environment configuration"}
                    </p>
                  </div>
                  {apiMode === "user" && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      ✓ Connected
                    </div>
                  )}
                </div>

                {/* API Key Input */}
                {!isApiConnected && (
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-black dark:text-white block mb-2">
                        TwelveLabs API Key
                      </label>
                      <Input
                        type="password"
                        placeholder="tl_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        disabled={isConnecting}
                        className="bg-white dark:bg-black border-gray-300 dark:border-gray-700 text-black dark:text-white placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-black dark:focus:border-white"
                      />
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Get your API key from{" "}
                      <a 
                        href="https://twelvelabs.io" 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-black dark:text-white underline hover:no-underline"
                      >
                        twelvelabs.io
                      </a>
                    </p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 pt-2">
                  {!isApiConnected ? (
                    <>
                      <Button
                        variant="outline"
                        onClick={() => setIsDialogOpen(false)}
                        disabled={isConnecting}
                        className="border-gray-300 dark:border-gray-700 bg-white dark:bg-black text-black dark:text-white hover:bg-gray-50 dark:hover:bg-gray-900"
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleApiConnect}
                        disabled={isConnecting || !apiKey.trim()}
                        className="bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200 disabled:bg-gray-300 dark:disabled:bg-gray-700"
                      >
                        {isConnecting ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            Connecting
                          </>
                        ) : (
                          "Connect"
                        )}
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        variant="outline"
                        onClick={handleSwitchToDefault}
                        disabled={isConnecting}
                        className="border-gray-300 dark:border-gray-700 bg-white dark:bg-black text-black dark:text-white hover:bg-gray-50 dark:hover:bg-gray-900"
                      >
                        {isConnecting ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            Switching...
                          </>
                        ) : (
                          "Default Mode"
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setIsDialogOpen(false)}
                        disabled={isConnecting}
                        className="border-gray-300 dark:border-gray-700 bg-white dark:bg-black text-black dark:text-white hover:bg-gray-50 dark:hover:bg-gray-900"
                      >
                        Close
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      {/* Alert */}
      {alert && (
        <div className="px-6 py-2">
          <Alert
            className={`${
              alert.type === "error"
                ? "border-gray-800 dark:border-gray-200 bg-gray-100 dark:bg-gray-900 text-black dark:text-white"
                : alert.type === "success"
                  ? "border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-black dark:text-white"
                  : "border-gray-400 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 text-black dark:text-white"
            } shadow-sm`}
          >
            <AlertDescription className="font-medium">{alert.message}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* API Error Alert */}
      {apiError && (
        <div className="px-6 py-2">
          <Alert className="border-gray-800 dark:border-gray-200 bg-gray-100 dark:bg-gray-900 text-black dark:text-white shadow-sm">
            <AlertDescription className="font-medium">
              API Error: {apiError}
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex bg-background">
        {/* Left Panel - Models */}
        <div className="flex-1 flex flex-col bg-card/30 border-r border-border left-panel">
          <div className="border-b border-border px-6 py-4 flex items-center justify-between bg-card/50">
            <h2 className="text-lg font-medium text-green-600 dark:text-green-400">Models</h2>
            <Select value={leftModel} onValueChange={setLeftModel}>
              <SelectTrigger className="w-56 bg-card border-border hover:bg-accent hover:text-accent-foreground shadow-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-card border-border shadow-lg">
                {getAvailableLeftModels().map((model) => (
                  <SelectItem
                    key={model.value}
                    value={model.value}
                    className="hover:bg-accent hover:text-accent-foreground"
                  >
                    <div className="flex items-center justify-between w-full">
                      <span>{model.label}</span>
                      <Badge variant="outline" className="ml-2 text-xs border-border">
                        {model.provider}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Left Panel Content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {leftResponses.length === 0 ? (
              <div className="space-y-4">
                {leftSuggestions.map((suggestion, index) => (
                  <Card
                    key={index}
                    className="cursor-pointer hover:bg-accent/50 hover:text-accent-foreground transition-all duration-200 border-border bg-card/50 shadow-sm hover:shadow-md"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    <CardContent className="p-4 flex items-center gap-3">
                      {index === 0 && <Film className="w-5 h-5 text-muted-foreground" />}
                      {index === 1 && <Settings className="w-5 h-5 text-muted-foreground" />}
                      {index === 2 && <Star className="w-5 h-5 text-muted-foreground" />}
                      <span className="text-sm">{suggestion}</span>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {leftResponses.map((response, index) => (
                  <Card
                    key={index}
                    className={`${
                      response.isUser || response.model === "user"
                        ? "ml-auto max-w-[80%] bg-white dark:bg-white/10 border-border shadow-sm"
                        : "mr-auto max-w-[80%] bg-muted/50 border-border shadow-sm"
                    }`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={response.isUser || response.model === "user" ? "default" : "secondary"}
                            className="border-border text-xs font-medium"
                          >
                            {response.isUser || response.model === "user" ? "You" : `${response.model} Model`}
                          </Badge>
                          {/* Small model tag */}
                          {response.model && response.model !== "user" && (
                            <Badge
                              variant="outline"
                              className="text-xs font-mono bg-red-500 text-white border-red-600 px-3 py-1 font-bold"
                            >
                              {response.model}
                            </Badge>
                          )}
                          {/* Model info */}
                          {response.model && response.model !== "user" && (
                            <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                              Model: {response.model}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">{response.timestamp.toLocaleTimeString()}</span>
                        </div>
                      </div>
                      {response.isLoading ? (
                        <LoadingResponse response={response.response} timestamp={response.timestamp} />
                      ) : (
                        <div className={response.error ? "text-red-600 dark:text-red-400" : ""}>
                          <ResponseContent 
                            response={response.response} 
                            model={response.model} 
                            timestamp={response.timestamp} 
                            isLoading={response.isLoading}
                            isUser={response.isUser}
                            error={response.error}
                            performanceData={response.performanceData}
                            isStreaming={response.isStreaming}
                          />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Visual Divider */}
        <div className="w-px bg-border flex-shrink-0"></div>

        {/* Right Panel - Models */}
        <div className="flex-1 flex flex-col bg-card/30 right-panel">
          <div className="border-b border-border px-6 py-4 flex items-center justify-between bg-card/50">
            <h2 className="text-lg font-medium text-green-600 dark:text-green-400">Models</h2>
            <Select value={rightModel} onValueChange={setRightModel}>
              <SelectTrigger className="w-56 bg-card border-border hover:bg-accent hover:text-accent-foreground shadow-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-card border-border shadow-lg">
                {getAvailableRightModels().map((model) => (
                  <SelectItem
                    key={model.value}
                    value={model.value}
                    className="hover:bg-accent hover:text-accent-foreground"
                  >
                    <div className="flex items-center justify-between w-full">
                      <span>{model.label}</span>
                      <Badge variant="outline" className="ml-2 text-xs border-border">
                        {model.provider}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Right Panel Content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {rightResponses.length === 0 ? (
              <div className="space-y-4">
                {rightSuggestions.map((suggestion, index) => (
                  <Card
                    key={index}
                    className="cursor-pointer hover:bg-accent/50 hover:text-accent-foreground transition-all duration-200 border-border bg-card/50 shadow-sm hover:shadow-md"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    <CardContent className="p-4 flex items-center gap-3">
                      {index === 0 && <Film className="w-5 h-5 text-muted-foreground" />}
                      {index === 1 && <Settings className="w-5 h-5 text-muted-foreground" />}
                      {index === 2 && <Star className="w-5 h-5 text-muted-foreground" />}
                      <span className="text-sm">{suggestion}</span>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {rightResponses.map((response, index) => (
                  <Card
                    key={index}
                    className={`${
                      response.isUser || response.model === "user"
                        ? "ml-auto max-w-[80%] bg-white dark:bg-white/10 border-border shadow-sm"
                        : "mr-auto max-w-[80%] bg-muted/50 border-border shadow-sm"
                    }`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={response.isUser || response.model === "user" ? "default" : "secondary"}
                            className="border-border text-xs font-medium"
                          >
                            {response.isUser || response.model === "user" ? "You" : `${response.model} Model`}
                          </Badge>
                          {/* Small model tag */}
                          {response.model && response.model !== "user" && (
                            <Badge
                              variant="outline"
                              className="text-xs font-mono bg-red-500 text-white border-red-600 px-3 py-1 font-bold"
                            >
                              {response.model}
                            </Badge>
                          )}
                          {/* Model info */}
                          {response.model && response.model !== "user" && (
                            <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                              Model: {response.model}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">{response.timestamp.toLocaleTimeString()}</span>
                        </div>
                      </div>
                      {response.isLoading ? (
                        <LoadingResponse response={response.response} timestamp={response.timestamp} />
                      ) : (
                        <div className={response.error ? "text-red-600 dark:text-red-400" : ""}>
                          <ResponseContent 
                            response={response.response} 
                            model={response.model} 
                            timestamp={response.timestamp} 
                            isLoading={response.isLoading}
                            isUser={response.isUser}
                            error={response.error}
                            performanceData={response.performanceData}
                            isStreaming={response.isStreaming}
                          />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Chat Input */}
      <div className="p-6 border-t border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          {isVideoProcessing && (
            <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{videoProcessingStatus}</span>
            </div>
          )}
          <div className="flex gap-2 bg-card border border-border rounded-lg shadow-lg">
            <Input
              placeholder={
                isVideoProcessing
                  ? "Processing video..."
                  : selectedVideo
                    ? "Ask about this video..."
                    : "Select a video first..."
              }
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
              disabled={!selectedVideo || isLoading || isVideoProcessing}
              className="border-0 focus-visible:ring-0 bg-transparent"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!selectedVideo || !message.trim() || isLoading || isVideoProcessing}
              className="bg-green-600 hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-700"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
