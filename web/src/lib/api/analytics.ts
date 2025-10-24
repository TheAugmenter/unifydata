/**
 * Analytics API Client
 */

import { api } from "./client";

export interface DashboardStats {
  period_days: number;
  total_conversations: number;
  total_messages: number;
  total_searches: number;
  total_documents: number;
  total_data_sources: number;
  tokens: {
    input: number;
    output: number;
    total: number;
  };
  total_cost_usd: number;
  avg_response_time_ms: number;
}

export interface UsageDataPoint {
  period: string;
  count: number;
  cost_usd: number;
  tokens_input: number;
  tokens_output: number;
}

export interface ModelUsageStats {
  model: string;
  usage_count: number;
  tokens_input: number;
  tokens_output: number;
  tokens_total: number;
}

export interface EventTypeStats {
  event_type: string;
  count: number;
  cost_usd: number;
}

export const analyticsApi = {
  /**
   * Get dashboard statistics
   */
  async getDashboardStats(days = 30): Promise<DashboardStats> {
    const response = await api.get("/analytics/dashboard", {
      params: { days },
    });
    return response.data;
  },

  /**
   * Get usage over time for charts
   */
  async getUsageOverTime(
    days = 30,
    eventType?: string,
    interval: "day" | "week" | "month" = "day"
  ): Promise<UsageDataPoint[]> {
    const response = await api.get("/analytics/usage-over-time", {
      params: { days, event_type: eventType, interval },
    });
    return response.data;
  },

  /**
   * Get top models used
   */
  async getTopModels(days = 30, limit = 10): Promise<ModelUsageStats[]> {
    const response = await api.get("/analytics/models", {
      params: { days, limit },
    });
    return response.data;
  },

  /**
   * Get event type breakdown
   */
  async getEventBreakdown(days = 30): Promise<EventTypeStats[]> {
    const response = await api.get("/analytics/events", {
      params: { days },
    });
    return response.data;
  },

  /**
   * Export analytics data
   */
  async exportData(days = 30, format: "csv" | "json" = "csv"): Promise<Blob> {
    const response = await api.get("/analytics/export", {
      params: { days, format },
      responseType: "blob",
    });
    return response.data;
  },
};
