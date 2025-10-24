/**
 * TypeScript types for API models
 */

export interface User {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  avatar_url: string | null
  job_title: string | null
  role: 'admin' | 'user' | 'viewer'
  org_id: string
  is_email_verified: boolean
  onboarding_completed: boolean
  is_active: boolean
  last_login_at: string | null
  created_at: string
}

export interface Organization {
  id: string
  name: string
  slug: string
  logo_url: string | null
  website: string | null
  plan: 'trial' | 'starter' | 'professional' | 'enterprise'
  trial_ends_at: string | null
  subscription_status: string
  max_users: number
  max_data_sources: number
  monthly_search_limit: number
  current_users: number
  current_data_sources: number
  searches_this_month: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  company_name: string
}

export interface RegisterResponse {
  user: User
  organization: Organization
  tokens: TokenResponse
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  user: User
  organization: Organization
  tokens: TokenResponse
}

export interface ApiError {
  error: string
  message: string
}

export type DataSourceType = 'salesforce' | 'slack' | 'google_drive' | 'notion' | 'gmail'

export type DataSourceStatus = 'connected' | 'disconnected' | 'syncing' | 'error'

export interface DataSource {
  id: string
  type: DataSourceType
  name: string
  status: DataSourceStatus
  last_synced_at: string | null
  documents_indexed: number
  metadata: Record<string, any>
}

export interface DataSourcesListResponse {
  data_sources: DataSource[]
}

export interface ConnectDataSourceResponse {
  authorization_url: string
  state: string
}

export interface SyncDataSourceResponse {
  message: string
  source_id: string
  status: string
}
