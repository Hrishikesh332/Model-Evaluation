"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function TestApiPage() {
  const [apiKey, setApiKey] = useState('')
  const [status, setStatus] = useState<any>(null)
  const [indexes, setIndexes] = useState<any>(null)
  const [models, setModels] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const testConnect = async () => {
    if (!apiKey.trim()) return
    
    setLoading(true)
    try {
      const response = await fetch('/api/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'twelvelabs', api_key: apiKey })
      })
      
      const data = await response.json()
      setStatus(data)
      console.log('Connect response:', data)
    } catch (error) {
      console.error('Connect error:', error)
      setStatus({ error: 'Failed to connect' })
    } finally {
      setLoading(false)
    }
  }

  const testStatus = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/status')
      const data = await response.json()
      setStatus(data)
      console.log('Status response:', data)
    } catch (error) {
      console.error('Status error:', error)
      setStatus({ error: 'Failed to get status' })
    } finally {
      setLoading(false)
    }
  }

  const testIndexes = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/indexes')
      const data = await response.json()
      setIndexes(data)
      console.log('Indexes response:', data)
    } catch (error) {
      console.error('Indexes error:', error)
      setIndexes({ error: 'Failed to get indexes' })
    } finally {
      setLoading(false)
    }
  }

  const testModels = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/models')
      const data = await response.json()
      setModels(data)
      console.log('Models response:', data)
    } catch (error) {
      console.error('Models error:', error)
      setModels({ error: 'Failed to get models' })
    } finally {
      setLoading(false)
    }
  }

  const testDisconnect = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/disconnect', { method: 'POST' })
      const data = await response.json()
      setStatus(data)
      console.log('Disconnect response:', data)
    } catch (error) {
      console.error('Disconnect error:', error)
      setStatus({ error: 'Failed to disconnect' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">API Test Page</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>API Key Management</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter TwelveLabs API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <Button onClick={testConnect} disabled={loading || !apiKey.trim()}>
              Connect
            </Button>
          </div>
          
          <div className="flex gap-2">
            <Button onClick={testStatus} disabled={loading}>
              Check Status
            </Button>
            <Button onClick={testDisconnect} disabled={loading}>
              Disconnect
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Status</CardTitle>
        </CardHeader>
        <CardContent>
          {status && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span>Status:</span>
                <Badge variant={status.status === 'success' ? 'default' : 'destructive'}>
                  {status.status}
                </Badge>
              </div>
              {status.message && <p>Message: {status.message}</p>}
              {status.connected !== undefined && (
                <p>Connected: {status.connected ? 'Yes' : 'No'}</p>
              )}
              {status.source && <p>Source: {status.source}</p>}
              {status.type && <p>Type: {status.type}</p>}
              {status.error && <p className="text-red-600">Error: {status.error}</p>}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Endpoints</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button onClick={testIndexes} disabled={loading}>
              Test Indexes
            </Button>
            <Button onClick={testModels} disabled={loading}>
              Test Models
            </Button>
          </div>
          
          {indexes && (
            <div className="space-y-2">
              <h3 className="font-semibold">Indexes Response:</h3>
              <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
                {JSON.stringify(indexes, null, 2)}
              </pre>
            </div>
          )}
          
          {models && (
            <div className="space-y-2">
              <h3 className="font-semibold">Models Response:</h3>
              <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
                {JSON.stringify(models, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 