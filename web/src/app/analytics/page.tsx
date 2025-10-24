"use client";

import { useState } from "react";
import {
  BarChart3,
  MessageCircle,
  Search,
  Database,
  DollarSign,
  Clock,
  TrendingUp,
  FileText,
  Loader2,
} from "lucide-react";
import {
  useDashboardStats,
  useUsageOverTime,
  useTopModels,
  useEventBreakdown,
} from "@/hooks/use-analytics";

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);

  const { data: dashboardStats, isLoading: loadingStats } = useDashboardStats(days);
  const { data: usageData, isLoading: loadingUsage } = useUsageOverTime(days);
  const { data: modelStats, isLoading: loadingModels } = useTopModels(days);
  const { data: eventBreakdown, isLoading: loadingEvents } = useEventBreakdown(days);

  const formatCost = (cost: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(cost);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("en-US").format(num);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
              <p className="mt-2 text-gray-600">
                Usage insights and performance metrics
              </p>
            </div>

            {/* Time Range Selector */}
            <div className="flex gap-2">
              {[7, 30, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    days === d
                      ? "bg-blue-600 text-white"
                      : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  {d} days
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loadingStats ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Conversations */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Conversations</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {formatNumber(dashboardStats?.total_conversations || 0)}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <MessageCircle className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Messages</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {formatNumber(dashboardStats?.total_messages || 0)}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <FileText className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
              </div>

              {/* Searches */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Searches</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {formatNumber(dashboardStats?.total_searches || 0)}
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <Search className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </div>

              {/* Total Cost */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Cost</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {formatCost(dashboardStats?.total_cost_usd || 0)}
                    </p>
                  </div>
                  <div className="p-3 bg-yellow-50 rounded-lg">
                    <DollarSign className="w-6 h-6 text-yellow-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Secondary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* Documents */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <Database className="w-5 h-5 text-gray-400" />
                  <p className="text-sm font-medium text-gray-600">Total Documents</p>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {formatNumber(dashboardStats?.total_documents || 0)}
                </p>
              </div>

              {/* Data Sources */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="w-5 h-5 text-gray-400" />
                  <p className="text-sm font-medium text-gray-600">Connected Sources</p>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {formatNumber(dashboardStats?.total_data_sources || 0)}
                </p>
              </div>

              {/* Avg Response Time */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <Clock className="w-5 h-5 text-gray-400" />
                  <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {((dashboardStats?.avg_response_time_ms || 0) / 1000).toFixed(2)}s
                </p>
              </div>
            </div>

            {/* Token Usage */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Token Usage</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Input Tokens</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatNumber(dashboardStats?.tokens.input || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Output Tokens</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {formatNumber(dashboardStats?.tokens.output || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Tokens</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(dashboardStats?.tokens.total || 0)}
                  </p>
                </div>
              </div>
            </div>

            {/* Model Usage Stats */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Top Models */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Models Used</h3>
                {loadingModels ? (
                  <div className="flex items-center justify-center h-32">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                  </div>
                ) : modelStats && modelStats.length > 0 ? (
                  <div className="space-y-4">
                    {modelStats.map((model, index) => (
                      <div key={model.model} className="flex items-center gap-4">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-semibold text-sm">
                          {index + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate">{model.model}</p>
                          <p className="text-sm text-gray-500">
                            {formatNumber(model.usage_count)} uses · {formatNumber(model.tokens_total)} tokens
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No model data available</p>
                )}
              </div>

              {/* Event Type Breakdown */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Type Breakdown</h3>
                {loadingEvents ? (
                  <div className="flex items-center justify-center h-32">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                  </div>
                ) : eventBreakdown && eventBreakdown.length > 0 ? (
                  <div className="space-y-4">
                    {eventBreakdown.map((event) => (
                      <div key={event.event_type} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900 capitalize">
                            {event.event_type.replace("_", " ")}
                          </span>
                          <span className="text-sm text-gray-600">
                            {formatNumber(event.count)} events
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${Math.min(
                                (event.count / (eventBreakdown[0]?.count || 1)) * 100,
                                100
                              )}%`,
                            }}
                          />
                        </div>
                        <p className="text-xs text-gray-500">
                          Cost: {formatCost(event.cost_usd)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No event data available</p>
                )}
              </div>
            </div>

            {/* Usage Over Time - Simple Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Over Time</h3>
              {loadingUsage ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                </div>
              ) : usageData && usageData.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Events
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Input Tokens
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Output Tokens
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Cost
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {usageData.slice(0, 10).map((data) => (
                        <tr key={data.period} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(data.period).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatNumber(data.count)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {formatNumber(data.tokens_input)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {formatNumber(data.tokens_output)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {formatCost(data.cost_usd)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No usage data available</p>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
