/**
 * React Query hooks for Data Sources
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { dataSourcesApi } from '@/lib/api/data-sources'
import type { DataSourceType } from '@/lib/types'

const QUERY_KEY = ['data-sources']

/**
 * Hook to fetch all data sources
 */
export function useDataSources() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => dataSourcesApi.list(),
  })
}

/**
 * Hook to initiate OAuth connection for a data source
 */
export function useConnectDataSource() {
  return useMutation({
    mutationFn: (sourceType: DataSourceType) => dataSourcesApi.connect(sourceType),
    onSuccess: (data) => {
      // Redirect to OAuth authorization URL
      window.location.href = data.authorization_url
    },
    onError: (error: any) => {
      toast.error('Failed to initiate connection', {
        description: error.response?.data?.message || error.message,
      })
    },
  })
}

/**
 * Hook to disconnect a data source
 */
export function useDisconnectDataSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sourceId: string) => dataSourcesApi.disconnect(sourceId),
    onSuccess: () => {
      toast.success('Data source disconnected successfully')
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
    onError: (error: any) => {
      toast.error('Failed to disconnect data source', {
        description: error.response?.data?.message || error.message,
      })
    },
  })
}

/**
 * Hook to manually trigger data sync
 */
export function useSyncDataSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sourceId: string) => dataSourcesApi.sync(sourceId),
    onSuccess: (data) => {
      toast.success('Sync started successfully', {
        description: `Syncing data from ${data.source_id}`,
      })
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
    onError: (error: any) => {
      toast.error('Failed to start sync', {
        description: error.response?.data?.message || error.message,
      })
    },
  })
}
