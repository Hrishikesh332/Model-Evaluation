import { type NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { type, api_key } = body
    
    if (!type || !api_key) {
      return NextResponse.json({
        status: "error",
        message: "API key type and key are required"
      }, { status: 400 })
    }

    // Store the API key in a secure cookie for this session
    const cookieStore = cookies()
    const response = NextResponse.json({
      status: "success",
      message: "API key connected successfully",
      type: type
    })

    // Set secure cookie with the API key
    response.cookies.set(`${type}_api_key`, api_key, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: '/'
    })

    // Also set a flag to indicate user mode
    response.cookies.set('api_mode', 'user', {
      httpOnly: false, // Allow frontend to read this
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: '/'
    })

    return response
  } catch (error) {
    console.error("Failed to connect API key:", error)
    return NextResponse.json({ 
      status: "error",
      message: "Failed to connect API key" 
    }, { status: 500 })
  }
}
