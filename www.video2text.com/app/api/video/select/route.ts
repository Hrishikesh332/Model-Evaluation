import { type NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001"

export async function POST(request: NextRequest) {
  try {
    const cookieStore = cookies()
    const apiMode = cookieStore.get('api_mode')?.value
    const twelvelabsApiKey = cookieStore.get('twelvelabs_api_key')?.value

    console.log("[v0] Video Select API - API Mode:", apiMode)
    console.log("[v0] Video Select API - User API Key present:", !!twelvelabsApiKey)

    const body = await request.json()

    // Determine the source of the API key
    let source = "environment"
    if (apiMode === "user" && twelvelabsApiKey) {
      source = "user_session"
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }

    // If user has provided an API key, include it in the request
    if (source === "user_session" && twelvelabsApiKey) {
      headers["X-API-Key"] = twelvelabsApiKey
      console.log("[v0] Video Select API - Using user-provided API key")
    } else {
      console.log("[v0] Video Select API - Using environment API key")
    }

    const response = await fetch(`${API_BASE_URL}/api/video/select`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`)
    }

    const data = await response.json()
    
    // Add source information to the response
    const responseData = {
      ...data,
      source,
      message: source === "user_session" ? "Using user API key" : "Using environment API key"
    }
    
    return NextResponse.json(responseData)
  } catch (error) {
    console.error("Failed to select video:", error)
    return NextResponse.json({ 
      status: "error",
      message: "Failed to select video",
      error: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 })
  }
}
