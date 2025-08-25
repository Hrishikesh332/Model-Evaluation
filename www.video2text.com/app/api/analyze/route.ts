import { type NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000"

export async function POST(request: NextRequest) {
  try {
    const cookieStore = cookies()
    const body = await request.json()
    const apiMode = cookieStore.get('api_mode')?.value
    const twelvelabsApiKey = cookieStore.get('twelvelabs_api_key')?.value

    console.log("[v0] Analyze API - API Mode:", apiMode)
    console.log("[v0] Analyze API - User API Key present:", !!twelvelabsApiKey)
    console.log("[v0] Analyze API - Request body:", JSON.stringify(body, null, 2))

    // Determine the source of the API key
    let source = "environment"
    if (apiMode === "user" && twelvelabsApiKey) {
      source = "user_session"
    }

    let sessionCookies = ""

    if (body.video_id && body.index_id) {
      console.log("[v0] Analyze API - Selecting video before analyze:", body.video_id)

      const selectHeaders: Record<string, string> = {
        "Content-Type": "application/json",
      }

      // If user has provided an API key, include it in the select request
      if (source === "user_session" && twelvelabsApiKey) {
        selectHeaders["X-API-Key"] = twelvelabsApiKey
        console.log("[v0] Analyze API - Using user-provided API key for video selection")
      } else {
        console.log("[v0] Analyze API - Using environment API key for video selection")
      }

      try {
        const selectResponse = await fetch(`${API_BASE_URL}/api/video/select`, {
          method: "POST",
          headers: selectHeaders,
          body: JSON.stringify({
            index_id: body.index_id,
            video_id: body.video_id,
          }),
        })

        const setCookieHeader = selectResponse.headers.get("set-cookie")
        if (setCookieHeader) {
          sessionCookies = setCookieHeader
          console.log("[v0] Analyze API - Captured session cookies from video selection")
        }

        if (!selectResponse.ok) {
          console.error("[v0] Analyze API - Failed to select video:", await selectResponse.text())
          return NextResponse.json(
            { error: "Failed to select video before analysis" },
            { status: selectResponse.status },
          )
        } else {
          console.log("[v0] Analyze API - Video selected successfully")
        }
      } catch (selectError) {
        console.error("[v0] Analyze API - Error selecting video:", selectError)
        return NextResponse.json({ error: "Failed to select video before analysis" }, { status: 500 })
      }
    }

    const baseHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    }

    // If user has provided an API key, include it in all requests
    if (source === "user_session" && twelvelabsApiKey) {
      baseHeaders["X-API-Key"] = twelvelabsApiKey
      console.log("[v0] Analyze API - Using user-provided API key for analysis")
    } else {
      console.log("[v0] Analyze API - Using environment API key for analysis")
    }

    if (sessionCookies) {
      baseHeaders.Cookie = sessionCookies
    }

    if (body.models && Array.isArray(body.models) && body.models.length > 1) {
      console.log(
        "[v0] Analyze API - Attempting parallel streaming endpoint:",
        `${API_BASE_URL}/api/analyze/stream/parallel`,
      )

      const parallelRequestBody = {
        query: body.query,
        models: body.models,
        execution_mode: body.execution_mode || "parallel",
        compare_models: body.compare_models !== false,
        index_id: body.index_id,
        video_id: body.video_id,
      }
      console.log("[v0] Analyze API - Parallel request body:", JSON.stringify(parallelRequestBody, null, 2))

      try {
        const parallelStreamingHeaders = {
          ...baseHeaders,
          Accept: "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        }

        const parallelStreamingResponse = await fetch(`${API_BASE_URL}/api/analyze/stream/parallel`, {
          method: "POST",
          headers: parallelStreamingHeaders,
          body: JSON.stringify(parallelRequestBody),
        })

        console.log("[v0] Analyze API - Parallel streaming response status:", parallelStreamingResponse.status)
        console.log(
          "[v0] Analyze API - Parallel streaming response headers:",
          Object.fromEntries(parallelStreamingResponse.headers.entries()),
        )

        if (parallelStreamingResponse.ok) {
          const contentType = parallelStreamingResponse.headers.get("content-type")
          console.log("[v0] Analyze API - Parallel streaming response content type:", contentType)

          if (contentType && contentType.includes("text/event-stream")) {
            console.log("[v0] Analyze API - ✅ Successfully connected to parallel streaming endpoint")

            return new NextResponse(parallelStreamingResponse.body, {
              status: parallelStreamingResponse.status,
              headers: {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache, no-transform",
                Connection: "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "X-Accel-Buffering": "no",
              },
            })
          }
        }

        console.log("[v0] Analyze API - Parallel streaming endpoint not available, falling back to regular streaming")
      } catch (parallelStreamingError) {
        console.log(
          "[v0] Analyze API - Parallel streaming endpoint failed, falling back to regular streaming:",
          parallelStreamingError,
        )
      }
    }

    console.log("[v0] Analyze API - Attempting streaming endpoint:", `${API_BASE_URL}/api/analyze/stream`)

    try {
      const streamingHeaders = {
        ...baseHeaders,
        Accept: "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      }

      const streamingResponse = await fetch(`${API_BASE_URL}/api/analyze/stream`, {
        method: "POST",
        headers: streamingHeaders,
        body: JSON.stringify({
          query: body.query,
          model: body.model,
          index_id: body.index_id,
          video_id: body.video_id,
        }),
      })

      console.log("[v0] Analyze API - Streaming response status:", streamingResponse.status)
      console.log(
        "[v0] Analyze API - Streaming response headers:",
        Object.fromEntries(streamingResponse.headers.entries()),
      )

      if (streamingResponse.ok) {
        const contentType = streamingResponse.headers.get("content-type")
        console.log("[v0] Analyze API - Streaming response content type:", contentType)

        if (contentType && contentType.includes("text/event-stream")) {
          console.log("[v0] Analyze API - ✅ Successfully connected to streaming endpoint")

          return new NextResponse(streamingResponse.body, {
            status: streamingResponse.status,
            headers: {
              "Content-Type": "text/event-stream",
              "Cache-Control": "no-cache, no-transform",
              Connection: "keep-alive",
              "Access-Control-Allow-Origin": "*",
              "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
              "Access-Control-Allow-Headers": "Content-Type, Authorization",
              "X-Accel-Buffering": "no",
            },
          })
        }
      }

      console.log("[v0] Analyze API - Streaming endpoint not available, falling back to regular endpoint")
    } catch (streamingError) {
      console.log("[v0] Analyze API - Streaming endpoint failed, falling back to regular endpoint:", streamingError)
    }

    console.log("[v0] Analyze API - Using regular endpoint:", `${API_BASE_URL}/api/analyze`)

    const regularHeaders = {
      ...baseHeaders,
      Accept: "text/event-stream, application/json", // Request streaming first, JSON as fallback
      "Cache-Control": "no-cache",
    }

    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      headers: regularHeaders,
      body: JSON.stringify({
        query: body.query,
        model: body.model,
        execution_mode: body.execution_mode,
        compare_models: body.compare_models,
        index_id: body.index_id,
        video_id: body.video_id,
        stream: true, // Request streaming format
      }),
    })

    console.log("[v0] Analyze API - Regular response status:", response.status)
    console.log("[v0] Analyze API - Regular response headers:", Object.fromEntries(response.headers.entries()))

    const contentType = response.headers.get("content-type")
    console.log("[v0] Analyze API - Response content type:", contentType)

    if (response.ok && contentType && contentType.includes("text/event-stream")) {
      console.log("[v0] Analyze API - Regular endpoint returned streaming response")

      return new NextResponse(response.body, {
        status: response.status,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache, no-transform",
          Connection: "keep-alive",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
          "X-Accel-Buffering": "no",
        },
      })
    }

    if (!response.ok) {
      const errorText = await response.text()
      console.error("[v0] Analyze API - Backend error response:", {
        status: response.status,
        statusText: response.statusText,
        body: errorText,
      })

      return NextResponse.json(
        {
          error: "Failed to analyze video",
          details: errorText,
          status: response.status,
        },
        { status: response.status },
      )
    }

    try {
      const responseText = await response.text()
      console.log("[v0] Analyze API - Raw response text (first 500 chars):", responseText.substring(0, 500))

      const data = JSON.parse(responseText)
      console.log("[v0] Analyze API - Success response received (non-streaming)")
      return NextResponse.json(data)
    } catch (parseError) {
      console.error("[v0] Analyze API - JSON parse error:", parseError)
      console.error("[v0] Analyze API - Response was not valid JSON")

      const responseText = await response.text()
      return NextResponse.json(
        {
          error: "Response parsing failed",
          raw_response: responseText,
          parse_error: parseError instanceof Error ? parseError.message : String(parseError),
        },
        { status: 500 },
      )
    }
  } catch (error) {
    console.error("[v0] Analyze API - Exception:", error)
    return NextResponse.json({ error: "Failed to analyze video" }, { status: 500 })
  }
}
