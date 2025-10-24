'use client'

/**
 * Data Sources Management Page
 * Allows users to connect and manage their data sources
 */

import { useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { toast } from 'sonner'
import { Database, RefreshCw, Loader2 } from 'lucide-react'
import {
  useDataSources,
  useConnectDataSource,
  useDisconnectDataSource,
  useSyncDataSource,
} from '@/hooks/use-data-sources'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { DataSourceType, DataSource } from '@/lib/types'

// Data source connector configurations
const CONNECTORS: {
  type: DataSourceType
  name: string
  description: string
  icon: string
  color: string
}[] = [
  {
    type: 'salesforce',
    name: 'Salesforce',
    description: 'Connect your Salesforce CRM data',
    icon: '☁️',
    color: 'bg-blue-500',
  },
  {
    type: 'slack',
    name: 'Slack',
    description: 'Search across your Slack messages and files',
    icon: '💬',
    color: 'bg-purple-500',
  },
  {
    type: 'google_drive',
    name: 'Google Drive',
    description: 'Access documents from Google Drive',
    icon: '📁',
    color: 'bg-yellow-500',
  },
  {
    type: 'notion',
    name: 'Notion',
    description: 'Search through your Notion workspace',
    icon: '📝',
    color: 'bg-gray-800',
  },
  {
    type: 'gmail',
    name: 'Gmail',
    description: 'Search your email conversations',
    icon: '📧',
    color: 'bg-red-500',
  },
]

export default function DataSourcesPage() {
  const searchParams = useSearchParams()
  const { data: dataSources, isLoading, error } = useDataSources()
  const connectMutation = useConnectDataSource()
  const disconnectMutation = useDisconnectDataSource()
  const syncMutation = useSyncDataSource()

  // Handle OAuth callback status
  useEffect(() => {
    const status = searchParams.get('status')
    const source = searchParams.get('source')
    const message = searchParams.get('message')

    if (status === 'success' && source) {
      toast.success(`Successfully connected ${source}!`)
      // Clear URL parameters
      window.history.replaceState({}, '', '/data-sources')
    } else if (status === 'error' && source) {
      toast.error(`Failed to connect ${source}`, {
        description: message || 'Please try again',
      })
      // Clear URL parameters
      window.history.replaceState({}, '', '/data-sources')
    }
  }, [searchParams])

  const handleConnect = (sourceType: DataSourceType) => {
    connectMutation.mutate(sourceType)
  }

  const handleDisconnect = (sourceId: string) => {
    if (confirm('Are you sure you want to disconnect this data source?')) {
      disconnectMutation.mutate(sourceId)
    }
  }

  const handleSync = (sourceId: string) => {
    syncMutation.mutate(sourceId)
  }

  const getConnectedSource = (type: DataSourceType): DataSource | undefined => {
    return dataSources?.find((source) => source.type === type)
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-semibold text-destructive">Failed to load data sources</p>
          <p className="text-sm text-muted-foreground">Please try again later</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Data Sources</h1>
        <p className="text-muted-foreground">
          Connect your data sources to enable unified search across all your tools
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {CONNECTORS.map((connector) => {
          const connectedSource = getConnectedSource(connector.type)
          const isConnected = !!connectedSource
          const isSyncing = connectedSource?.status === 'syncing'

          return (
            <Card key={connector.type} className="relative overflow-hidden">
              <div className={`absolute left-0 top-0 h-1 w-full ${connector.color}`} />
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="text-4xl">{connector.icon}</div>
                    <div>
                      <CardTitle>{connector.name}</CardTitle>
                      <CardDescription>{connector.description}</CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isConnected ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <div
                        className={`h-2 w-2 rounded-full ${
                          isSyncing
                            ? 'bg-yellow-500'
                            : connectedSource.status === 'connected'
                            ? 'bg-green-500'
                            : 'bg-red-500'
                        }`}
                      />
                      <span className="capitalize text-muted-foreground">
                        {connectedSource.status}
                      </span>
                    </div>

                    {connectedSource.last_synced_at && (
                      <p className="text-xs text-muted-foreground">
                        Last synced: {new Date(connectedSource.last_synced_at).toLocaleString()}
                      </p>
                    )}

                    <p className="text-xs text-muted-foreground">
                      {connectedSource.documents_indexed} documents indexed
                    </p>

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSync(connectedSource.id)}
                        disabled={isSyncing || syncMutation.isPending}
                        className="flex-1"
                      >
                        {syncMutation.isPending ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <RefreshCw className="mr-2 h-4 w-4" />
                        )}
                        Sync
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDisconnect(connectedSource.id)}
                        disabled={disconnectMutation.isPending}
                      >
                        Disconnect
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button
                    onClick={() => handleConnect(connector.type)}
                    disabled={connectMutation.isPending}
                    className="w-full"
                  >
                    {connectMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Connecting...
                      </>
                    ) : (
                      <>
                        <Database className="mr-2 h-4 w-4" />
                        Connect
                      </>
                    )}
                  </Button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
