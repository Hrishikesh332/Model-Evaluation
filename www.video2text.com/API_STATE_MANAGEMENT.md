# API State Management System

## Overview

The frontend now has a robust API state management system that properly handles both user-provided API keys and environment-based API keys for TwelveLabs integration.

## Key Features

### 1. Dual API Key Support
- **User Mode**: When a user provides their own API key through the UI
- **Environment Mode**: When using API keys configured in environment variables (default)

### 2. Secure Cookie-Based Storage
- API keys are stored in secure HTTP-only cookies
- No sensitive data in localStorage or client-side state
- Automatic session management

### 3. Automatic Fallback
- If no user API key is provided, the system automatically falls back to environment variables
- Seamless switching between modes

## API Routes

### `/api/connect` (POST)
Connects a user-provided API key and stores it in secure cookies.

**Request Body:**
```json
{
  "type": "twelvelabs",
  "api_key": "user_api_key_here"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "API key connected successfully",
  "type": "twelvelabs"
}
```

### `/api/disconnect` (POST)
Disconnects the current API key and clears all related cookies.

**Response:**
```json
{
  "status": "success",
  "message": "API key disconnected successfully"
}
```

### `/api/status` (GET)
Returns the current API connection status and mode.

**Response:**
```json
{
  "status": "success",
  "connected": true,
  "type": "twelvelabs",
  "source": "user_session",
  "message": "Connected using user API key"
}
```

### `/api/indexes` (GET)
Fetches video indexes. Automatically uses the appropriate API key source.

**Response:**
```json
{
  "indexes": [...],
  "source": "user_session",
  "message": "Using user API key"
}
```

### `/api/indexes/[id]/videos` (GET)
Fetches videos for a specific index. Automatically uses the appropriate API key source.

### `/api/models` (GET)
Fetches available AI models. Automatically uses the appropriate API key source.

### `/api/video/select` (POST)
Selects a video for analysis. Automatically uses the appropriate API key source.

### `/api/analyze` (POST)
Analyzes videos using AI models. Automatically uses the appropriate API key source.

## Frontend Integration

### Custom Hook: `useApiState`

The `useApiState` hook provides a clean interface for managing API state:

```typescript
import { useApiState } from '@/hooks/use-api-state'

function MyComponent() {
  const {
    isConnected,
    apiMode,
    isApiConnected,
    isLoading,
    error,
    checkApiStatus,
    connectApiKey,
    disconnectApiKey
  } = useApiState()

  // Use the hook methods and state
}
```

### State Variables

- `isConnected`: Whether the API is connected (either mode)
- `apiMode`: Current mode ('default' | 'user')
- `isApiConnected`: Whether using user-provided API key
- `isLoading`: Loading state for API operations
- `error`: Any error messages

### Methods

- `checkApiStatus()`: Check current API connection status
- `connectApiKey(type, key)`: Connect a new API key
- `disconnectApiKey()`: Disconnect current API key

## How It Works

### 1. Initialization
On app startup, the system:
1. Checks for existing API key cookies
2. Determines the current mode (user vs environment)
3. Sets the appropriate state

### 2. User API Key Connection
When a user provides an API key:
1. Key is sent to `/api/connect`
2. Key is stored in secure HTTP-only cookie
3. `api_mode` cookie is set to 'user'
4. Frontend state is updated

### 3. API Requests
All API requests automatically:
1. Check the current API mode
2. Include the appropriate API key in headers
3. Fall back to environment variables if no user key

### 4. Disconnection
When disconnecting:
1. All API key cookies are cleared
2. System falls back to environment variables
3. Frontend state is reset

## Security Features

- **HTTP-only cookies**: API keys are not accessible via JavaScript
- **Secure cookies**: In production, cookies are only sent over HTTPS
- **SameSite strict**: Prevents CSRF attacks
- **Automatic expiration**: Cookies expire after 7 days
- **No localStorage**: Sensitive data is never stored in browser storage

## Testing

Use the test page at `/test-api` to verify:
- API key connection/disconnection
- Status checking
- Endpoint functionality
- Cookie management

## Environment Variables

The backend should have these environment variables configured:
- `TWELVELABS_API_KEY`: Default API key for environment mode
- `GEMINI_API_KEY`: Gemini API key (if using)
- `OPENAI_API_KEY`: OpenAI API key (if using)

## Error Handling

The system provides comprehensive error handling:
- Network errors
- Authentication failures
- Invalid API keys
- Backend service errors

All errors are logged and displayed to users with appropriate messages.

## Migration Notes

- Removed localStorage usage for API keys
- Updated all API routes to handle dual key sources
- Added automatic fallback to environment variables
- Improved error handling and user feedback
- Added comprehensive logging for debugging 