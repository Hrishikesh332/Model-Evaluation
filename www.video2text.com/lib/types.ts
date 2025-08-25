export interface ModelResponse {
  id: string
  query: string
  response: string
  model: string
  timestamp: Date
  isLoading?: boolean
  error?: boolean
  isUser?: boolean
  performanceData?: any
}
