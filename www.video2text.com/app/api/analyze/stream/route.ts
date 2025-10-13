import { type NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001"

export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const body = await request.json()
    
    // Check if we have API keys in cookies (user mode)
    const twelvelabsKey = cookieStore.get('twelvelabs_api_key')?.value
    const apiMode = cookieStore.get('api_mode')?.value

    // If we have user API keys, proxy to backend with those keys
    if (apiMode === 'user' && twelvelabsKey) {
      const response = await fetch(`${API_BASE_URL}/api/analyze/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'X-TwelveLabs-API-Key': twelvelabsKey,
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        throw new Error(`Backend responded with status: ${response.status}`)
      }

      // Return the streaming response directly
      return new NextResponse(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      })
    }

    // If no user keys, check environment mode
    const response = await fetch(`${API_BASE_URL}/api/analyze/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    // Return the streaming response directly
    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error("Failed to analyze video (streaming):", error)
    return NextResponse.json({ 
      status: "error",
      message: "Failed to analyze video",
      error: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 })
  }
}
