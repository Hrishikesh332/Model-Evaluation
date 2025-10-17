import { type NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ indexId: string; videoId: string }> }
) {
  try {
    const cookieStore = await cookies()
    const { indexId, videoId } = await params
    
    // Check if we have API keys in cookies (user mode)
    const twelvelabsKey = cookieStore.get('twelvelabs_api_key')?.value
    const apiMode = cookieStore.get('api_mode')?.value

    // Prepare headers for the backend request
    const headers: Record<string, string> = {
      'Accept': 'image/jpeg',
    }

    // Add API key if available
    if (apiMode === 'user' && twelvelabsKey) {
      headers['X-TwelveLabs-API-Key'] = twelvelabsKey
    }

    // Proxy the thumbnail request to the backend
    const response = await fetch(`${API_BASE_URL}/api/thumbnails/${indexId}/${videoId}`, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    // Get the image data
    const imageBuffer = await response.arrayBuffer()
    
    // Return the image with proper headers
    return new NextResponse(imageBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'image/jpeg',
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
      },
    })
  } catch (error) {
    console.error("Failed to get thumbnail:", error)
    return NextResponse.json({ 
      status: "error",
      message: "Failed to get thumbnail",
      error: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 })
  }
}