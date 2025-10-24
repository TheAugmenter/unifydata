/**
 * React Query hooks for Analytics
 */

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api/analytics";

/**
 * Hook for dashboard statistics
 */
export function useDashboardStats(days = 30) {
  return useQuery({
    queryKey: ["analytics-dashboard", days],
    queryFn: () => analyticsApi.getDashboardStats(days),
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook for usage over time data
 */
export function useUsageOverTime(
  days = 30,
  eventType?: string,
  interval: "day" | "week" | "month" = "day"
) {
  return useQuery({
    queryKey: ["analytics-usage-over-time", days, eventType, interval],
    queryFn: () => analyticsApi.getUsageOverTime(days, eventType, interval),
    staleTime: 60000,
  });
}

/**
 * Hook for top models used
 */
export function useTopModels(days = 30, limit = 10) {
  return useQuery({
    queryKey: ["analytics-models", days, limit],
    queryFn: () => analyticsApi.getTopModels(days, limit),
    staleTime: 60000,
  });
}

/**
 * Hook for event type breakdown
 */
export function useEventBreakdown(days = 30) {
  return useQuery({
    queryKey: ["analytics-events", days],
    queryFn: () => analyticsApi.getEventBreakdown(days),
    staleTime: 60000,
  });
}
