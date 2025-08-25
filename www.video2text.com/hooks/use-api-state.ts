import { useState, useEffect, useCallback } from 'react'
import { apiService } from '@/lib/api'

export interface ApiState {
  isConnected: boolean
  apiMode: 'default' | 'user'
  isApiConnected: boolean
  isLoading: boolean
  error: string | null
}

export function useApiState() {
  const [state, setState] = useState<ApiState>({
    isConnected: false,
    apiMode: 'default',
    isApiConnected: false,
    isLoading: true,
    error: null
  })

  const checkApiStatus = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const apiStatus = await apiService.checkApiKeyStatus()
      console.log('[useApiState] API status:', apiStatus)
      
      const newState: ApiState = {
        isConnected: apiStatus.connected,
        apiMode: apiStatus.source === 'user_session' ? 'user' : 'default',
        isApiConnected: apiStatus.source === 'user_session',
        isLoading: false,
        error: null
      }
      
      setState(newState)
      return newState
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to check API status'
      console.error('[useApiState] Error checking API status:', error)
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }))
      
      throw error
    }
  }, [])

  const connectApiKey = useCallback(async (type: string, apiKey: string) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      await apiService.connectApiKey(type as any, apiKey)
      
      // Wait a moment for the cookie to be set
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Check the new status
      await checkApiStatus()
      
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to connect API key'
      console.error('[useApiState] Error connecting API key:', error)
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }))
      
      throw error
    }
  }, [checkApiStatus])

  const disconnectApiKey = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      await apiService.disconnectApiKey()
      
      // Wait a moment for the cookie to be cleared
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Check the new status
      await checkApiStatus()
      
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to disconnect API key'
      console.error('[useApiState] Error disconnecting API key:', error)
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }))
      
      throw error
    }
  }, [checkApiStatus])

  // Initialize API state on mount
  useEffect(() => {
    checkApiStatus()
  }, [checkApiStatus])

  return {
    ...state,
    checkApiStatus,
    connectApiKey,
    disconnectApiKey
  }
} 