/**
 * Data Sources API Service
 * Handles all data source related API calls
 */

import { apiClient } from '../api-client'
import type {
  DataSource,
  DataSourcesListResponse,
  ConnectDataSourceResponse,
  SyncDataSourceResponse,
  DataSourceType,
} from '../types'

export const dataSourcesApi = {
  /**
   * Get list of all connected data sources for current user
   */
  async list(): Promise<DataSource[]> {
    const { data } = await apiClient.get<DataSourcesListResponse>('/datasources/')
    return data.data_sources
  },

  /**
   * Initiate OAuth connection flow for a data source
   * Returns authorization URL to redirect user to
   */
  async connect(sourceType: DataSourceType): Promise<ConnectDataSourceResponse> {
    const { data } = await apiClient.get<ConnectDataSourceResponse>(
      `/datasources/${sourceType}/connect`
    )
    return data
  },

  /**
   * Disconnect and remove a data source
   */
  async disconnect(sourceId: string): Promise<void> {
    await apiClient.delete(`/datasources/${sourceId}`)
  },

  /**
   * Manually trigger data sync for a data source
   */
  async sync(sourceId: string): Promise<SyncDataSourceResponse> {
    const { data} = await apiClient.post<SyncDataSourceResponse>(
      `/datasources/${sourceId}/sync`
    )
    return data
  },
}
