import { NextResponse } from "next/server"
import { cookies } from "next/headers"

export async function POST() {
  try {
    const cookieStore = cookies()
    
    // Clear all API key related cookies
    cookieStore.delete("twelvelabs_api_key")
    cookieStore.delete("gemini_api_key")
    cookieStore.delete("openai_api_key")
    cookieStore.delete("api_mode")

    const response = NextResponse.json({
      status: "success",
      message: "API key disconnected successfully",
    })

    // Also clear cookies from response
    response.cookies.delete("twelvelabs_api_key")
    response.cookies.delete("gemini_api_key")
    response.cookies.delete("openai_api_key")
    response.cookies.delete("api_mode")

    return response
  } catch (error) {
    console.error("Failed to disconnect API key:", error)
    return NextResponse.json(
      {
        status: "error",
        message: "Failed to disconnect API key",
      },
      { status: 500 },
    )
  }
}
