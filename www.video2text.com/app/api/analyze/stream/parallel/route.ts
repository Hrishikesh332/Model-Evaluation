import { type NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001"

export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const body = await request.json()
    
    // Check if we have API keys in cookies (user mode)
    const twelvelabsKey = cookieStore.get('twelvelabs_api_key')?.value
    const geminiKey = cookieStore.get('gemini_api_key')?.value
    const openaiKey = cookieStore.get('openai_api_key')?.value
    const apiMode = cookieStore.get('api_mode')?.value

    // Prepare headers for the backend request
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    }

    // If we have user API keys, add them to headers
    if (apiMode === 'user') {
      if (twelvelabsKey) {
        headers['X-TwelveLabs-API-Key'] = twelvelabsKey
      }
      if (geminiKey) {
        headers['X-Gemini-API-Key'] = geminiKey
      }
      if (openaiKey) {
        headers['X-OpenAI-API-Key'] = openaiKey
      }
    }

    // Make request to backend parallel streaming endpoint
    const response = await fetch(`${API_BASE_URL}/api/analyze/stream/parallel`, {
      method: 'POST',
      headers,
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
    console.error("Failed to analyze video in parallel:", error)
    return NextResponse.json({ 
      status: "error",
      message: "Failed to analyze video in parallel",
      error: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 })
  }
}
