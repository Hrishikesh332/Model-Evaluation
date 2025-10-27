"use client"

import React, { useState } from 'react'
import { VideoPlayer } from '@/components/video-player'
import { Button } from '@/components/ui/button'

export default function VideoPlayerTest() {
  const [isOpen, setIsOpen] = useState(false)
  
  // Sample HLS URL for testing
  const testVideoUrl = "https://deuqpmn4rs7j5.cloudfront.net/67ca0ec8d29800ecabf27d70/68fe49b8db62b062a0c024ec/stream/4eeffd69-71fc-45db-8f51-d1a19a5532a7.m3u8"
  
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-2xl font-bold">Video Player Test</h1>
        <p className="text-muted-foreground">Testing the HLS video player component</p>
        
        <Button onClick={() => setIsOpen(true)}>
          Open Video Player
        </Button>
        
        <div className="text-sm text-muted-foreground">
          <p>Video URL: {testVideoUrl}</p>
        </div>
        
        <VideoPlayer
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          videoUrl={testVideoUrl}
          videoTitle="Test Video"
        />
      </div>
    </div>
  )
}
