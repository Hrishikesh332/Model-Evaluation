"use client"

import React, { useEffect, useRef, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { X, Play, Pause, Volume2, VolumeX, Maximize, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'

interface VideoPlayerProps {
  isOpen: boolean
  onClose: () => void
  videoUrl: string
  videoTitle?: string
}

export function VideoPlayer({ isOpen, onClose, videoUrl, videoTitle }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showControls, setShowControls] = useState(true)
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Load HLS.js dynamically
  useEffect(() => {
    if (!isOpen || !videoUrl) return

    const loadHLS = async () => {
      try {
        // Dynamically import HLS.js
        const Hls = (await import('hls.js')).default
        
        if (!videoRef.current) return

        const video = videoRef.current
        
        // Clear any existing error
        setError(null)
        setIsLoading(true)

        if (Hls.isSupported()) {
          const hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
            backBufferLength: 90
          })
          
          hls.loadSource(videoUrl)
          hls.attachMedia(video)
          
          hls.on(Hls.Events.MANIFEST_PARSED, () => {
            console.log('HLS manifest parsed successfully')
            setIsLoading(false)
          })
          
          hls.on(Hls.Events.ERROR, (event, data) => {
            console.error('HLS error:', data)
            if (data.fatal) {
              switch (data.type) {
                case Hls.ErrorTypes.NETWORK_ERROR:
                  setError('Network error occurred while loading video')
                  break
                case Hls.ErrorTypes.MEDIA_ERROR:
                  setError('Media error occurred while playing video')
                  break
                default:
                  setError('Fatal error occurred while loading video')
                  break
              }
              setIsLoading(false)
            }
          })
          
          // Store HLS instance for cleanup
          ;(video as any).hls = hls
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          // Native HLS support (Safari)
          video.src = videoUrl
          video.addEventListener('loadedmetadata', () => {
            setIsLoading(false)
          })
          video.addEventListener('error', () => {
            setError('Failed to load video')
            setIsLoading(false)
          })
        } else {
          setError('HLS is not supported in this browser')
          setIsLoading(false)
        }
      } catch (err) {
        console.error('Failed to load HLS.js:', err)
        setError('Failed to load video player')
        setIsLoading(false)
      }
    }

    loadHLS()

    // Cleanup function
    return () => {
      if (videoRef.current) {
        const video = videoRef.current
        if ((video as any).hls) {
          ;(video as any).hls.destroy()
        }
        video.src = ''
        video.load()
      }
    }
  }, [isOpen, videoUrl])

  // Video event handlers
  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleTimeUpdate = () => setCurrentTime(video.currentTime)
    const handleDurationChange = () => setDuration(video.duration)
    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    const handleVolumeChange = () => {
      setVolume(video.volume)
      setIsMuted(video.muted)
    }
    const handleLoadStart = () => setIsLoading(true)
    const handleCanPlay = () => setIsLoading(false)
    const handleError = () => {
      setError('Failed to load video')
      setIsLoading(false)
    }

    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('durationchange', handleDurationChange)
    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)
    video.addEventListener('volumechange', handleVolumeChange)
    video.addEventListener('loadstart', handleLoadStart)
    video.addEventListener('canplay', handleCanPlay)
    video.addEventListener('error', handleError)

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('durationchange', handleDurationChange)
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
      video.removeEventListener('volumechange', handleVolumeChange)
      video.removeEventListener('loadstart', handleLoadStart)
      video.removeEventListener('canplay', handleCanPlay)
      video.removeEventListener('error', handleError)
    }
  }, [isOpen])

  // Auto-hide controls
  useEffect(() => {
    if (!isOpen) return

    const resetControlsTimeout = () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current)
      }
      setShowControls(true)
      controlsTimeoutRef.current = setTimeout(() => {
        if (isPlaying) {
          setShowControls(false)
        }
      }, 3000)
    }

    const handleMouseMove = () => resetControlsTimeout()
    const handleMouseLeave = () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current)
      }
      if (isPlaying) {
        setShowControls(false)
      }
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseleave', handleMouseLeave)
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current)
      }
    }
  }, [isOpen, isPlaying])

  const handleTimeUpdate = () => {
    const video = videoRef.current
    if (!video) return
    setCurrentTime(video.currentTime)
  }

  const handleDurationChange = () => {
    const video = videoRef.current
    if (!video) return
    setDuration(video.duration)
  }

  const togglePlay = () => {
    const video = videoRef.current
    if (!video) {
      console.log('No video element found')
      return
    }

    console.log('Toggle play clicked, current state:', isPlaying)
    console.log('Video paused state:', video.paused)
    
    if (isPlaying) {
      video.pause()
      console.log('Video paused')
      setIsPlaying(false)
    } else {
      video.play().then(() => {
        console.log('Video playing successfully')
        setIsPlaying(true)
      }).catch((error) => {
        console.error('Error playing video:', error)
        setIsPlaying(false)
      })
    }
  }

  const toggleMute = () => {
    const video = videoRef.current
    if (!video) return

    video.muted = !video.muted
    setIsMuted(video.muted)
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current
    if (!video) return

    const newVolume = parseFloat(e.target.value)
    video.volume = newVolume
    video.muted = newVolume === 0
    setVolume(newVolume)
    setIsMuted(newVolume === 0)
  }

  const restartVideo = () => {
    const video = videoRef.current
    if (!video) return

    video.currentTime = 0
    video.play().catch((error) => {
      console.error('Error restarting video:', error)
    })
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current
    if (!video) return

    const newTime = parseFloat(e.target.value)
    video.currentTime = newTime
    setCurrentTime(newTime)
  }

  const toggleFullscreen = () => {
    const video = videoRef.current
    if (!video) return

    if (!document.fullscreenElement) {
      video.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const handleClose = () => {
    const video = videoRef.current
    if (video) {
      video.pause()
      video.currentTime = 0
    }
    onClose()
  }

  if (!isOpen) return null

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl w-full p-0 bg-black border-2 border-gray-800 rounded-[58px] overflow-hidden shadow-2xl [&>button]:hidden">
        <DialogHeader className="absolute top-4 left-4 z-10">
          <DialogTitle className="text-white text-lg font-semibold">
            {videoTitle || 'Video Player'}
          </DialogTitle>
        </DialogHeader>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClose}
          className="absolute top-6 right-6 z-50 text-white hover:bg-green-500/30 hover:text-green-400 bg-black/90 rounded-full p-4 border-2 border-white shadow-xl"
        >
          <X className="w-8 h-8" />
        </Button>

        <div className="relative w-full aspect-video bg-black rounded-[58px] overflow-hidden">
          {/* Backup X button inside video container */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            className="absolute top-4 right-4 z-40 text-white hover:bg-green-500/30 hover:text-green-400 bg-black/90 rounded-full p-3 border-2 border-white shadow-xl"
          >
            <X className="w-6 h-6" />
          </Button>
          
          {error ? (
            <div className="flex items-center justify-center h-full text-white">
              <div className="text-center">
                <p className="text-lg mb-4">Error loading video</p>
                <p className="text-sm text-gray-400 mb-4">{error}</p>
                <Button onClick={handleClose} variant="outline">
                  Close
                </Button>
              </div>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                className="w-full h-full object-cover rounded-[58px]"
                onDoubleClick={toggleFullscreen}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleDurationChange}
              />
              
              {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <div className="text-white text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                    <p>Loading video...</p>
                  </div>
                </div>
              )}

              {/* Video Controls */}
              <div
                className={cn(
                  "absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity duration-300",
                  showControls ? "opacity-100" : "opacity-0"
                )}
                onMouseEnter={() => setShowControls(true)}
                onMouseLeave={() => {
                  if (isPlaying) {
                    controlsTimeoutRef.current = setTimeout(() => setShowControls(false), 3000)
                  }
                }}
              >
                {/* Progress Bar */}
                <div className="mb-4">
                  <input
                    type="range"
                    min="0"
                    max={duration || 0}
                    value={currentTime}
                    onChange={handleSeek}
                    className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
                    style={{
                      background: `linear-gradient(to right, #22c55e 0%, #22c55e ${(currentTime / duration) * 100}%, #4b5563 ${(currentTime / duration) * 100}%, #4b5563 100%)`
                    }}
                  />
                </div>

                {/* Control Buttons */}
                <div className="flex items-center justify-between text-white">
                  <div className="flex items-center space-x-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        console.log('Play/Pause button clicked!')
                        togglePlay()
                      }}
                      className="text-white hover:bg-green-500/20 hover:text-green-400 bg-black/20 border border-green-500 rounded-md px-3 py-2 min-w-[50px]"
                    >
                      {isPlaying ? (
                        <Pause className="w-5 h-5" />
                      ) : (
                        <Play className="w-5 h-5" />
                      )}
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={restartVideo}
                      className="text-white hover:bg-green-500/20 hover:text-green-400"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </Button>

                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={toggleMute}
                        className="text-white hover:bg-green-500/20 hover:text-green-400"
                      >
                        {isMuted || volume === 0 ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                      </Button>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={volume}
                        onChange={handleVolumeChange}
                        className="w-20 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
                        style={{
                          background: `linear-gradient(to right, #16a34a 0%, #16a34a ${volume * 100}%, #4b5563 ${volume * 100}%, #4b5563 100%)`
                        }}
                      />
                    </div>

                    <span className="text-sm">
                      {formatTime(currentTime)} / {formatTime(duration)}
                    </span>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleFullscreen}
                    className="text-white hover:bg-green-500/20 hover:text-green-400"
                  >
                    <Maximize className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
