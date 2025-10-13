import { type NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const cookieStore = await cookies()
    const { id: indexId } = await params
    
    // Check if we have API keys in cookies (user mode)
    const twelvelabsKey = cookieStore.get('twelvelabs_api_key')?.value
    const apiMode = cookieStore.get('api_mode')?.value

    // If we have user API keys, proxy to backend with those keys
    if (apiMode === 'user' && twelvelabsKey) {
      const response = await fetch(`${API_BASE_URL}/api/indexes/${indexId}/videos`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-TwelveLabs-API-Key': twelvelabsKey,
        },
      })

      if (!response.ok) {
        throw new Error(`Backend responded with status: ${response.status}`)
      }

      const data = await response.json()
      return NextResponse.json(data)
    }

    // If no user keys, check environment mode
    const response = await fetch(`${API_BASE_URL}/api/indexes/${indexId}/videos`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Failed to get videos:", error)
    return NextResponse.json({ 
      status: "error",
      message: "Failed to get videos",
      error: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 })
  }
}