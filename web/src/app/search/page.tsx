"use client";

import { useState, useEffect } from "react";
import { Search, Filter, ExternalLink, Clock, FileText } from "lucide-react";
import { useSearch, useSearchWithSummary } from "@/hooks/use-search";
import { SearchRequest, SearchResultItem } from "@/lib/api/search";
import { toast } from "sonner";

// Source type icons and colors
const SOURCE_CONFIG = {
  salesforce: {
    name: "Salesforce",
    icon: "📊",
    color: "text-blue-600 bg-blue-50",
  },
  slack: {
    name: "Slack",
    icon: "💬",
    color: "text-purple-600 bg-purple-50",
  },
  google_drive: {
    name: "Google Drive",
    icon: "📁",
    color: "text-green-600 bg-green-50",
  },
  gmail: {
    name: "Gmail",
    icon: "📧",
    color: "text-red-600 bg-red-50",
  },
  notion: {
    name: "Notion",
    icon: "📝",
    color: "text-gray-600 bg-gray-50",
  },
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [searchTime, setSearchTime] = useState(0);
  const [totalResults, setTotalResults] = useState(0);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [minScore, setMinScore] = useState(0.7);
  const [showFilters, setShowFilters] = useState(false);
  const [useAiSummary, setUseAiSummary] = useState(false);
  const [aiSummary, setAiSummary] = useState<any>(null);

  const searchMutation = useSearch();
  const searchWithSummaryMutation = useSearchWithSummary();

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    if (!query.trim()) {
      toast.error("Please enter a search query");
      return;
    }

    const searchRequest: SearchRequest = {
      query: query.trim(),
      limit: 20,
      source_types: selectedSources.length > 0 ? selectedSources : undefined,
      min_score: minScore,
    };

    try {
      if (useAiSummary) {
        const result = await searchWithSummaryMutation.mutateAsync(searchRequest);
        setSearchResults(result.results);
        setSearchTime(result.search_time_seconds);
        setTotalResults(result.total_results);
        setAiSummary(result.ai_summary);
      } else {
        const result = await searchMutation.mutateAsync(searchRequest);
        setSearchResults(result.results);
        setSearchTime(result.search_time_seconds);
        setTotalResults(result.total_results);
        setAiSummary(null);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Search failed");
    }
  };

  const toggleSource = (source: string) => {
    setSelectedSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    );
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatScore = (score: number) => {
    return `${Math.round(score * 100)}%`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Search</h1>
          <p className="mt-2 text-gray-600">
            AI-powered search across all your connected data sources
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search across all your data sources..."
                  className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                className="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <Filter className="w-5 h-5" />
                Filters
              </button>
              <button
                type="submit"
                disabled={searchMutation.isPending || searchWithSummaryMutation.isPending}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {searchMutation.isPending || searchWithSummaryMutation.isPending
                  ? "Searching..."
                  : "Search"}
              </button>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="pt-4 border-t border-gray-200 space-y-4">
                {/* Source Type Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Data Sources
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(SOURCE_CONFIG).map(([key, config]) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => toggleSource(key)}
                        className={`px-4 py-2 rounded-lg border transition-colors ${
                          selectedSources.includes(key)
                            ? "bg-blue-50 border-blue-500 text-blue-700"
                            : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        <span className="mr-2">{config.icon}</span>
                        {config.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Min Score Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Minimum Relevance: {formatScore(minScore)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={minScore}
                    onChange={(e) => setMinScore(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                {/* AI Summary Toggle */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="ai-summary"
                    checked={useAiSummary}
                    onChange={(e) => setUseAiSummary(e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="ai-summary" className="text-sm text-gray-700">
                    Generate AI summary of results
                  </label>
                </div>
              </div>
            )}
          </form>
        </div>

        {/* Search Results */}
        {totalResults > 0 && (
          <div className="mb-4 flex items-center justify-between">
            <p className="text-gray-600">
              Found <span className="font-semibold text-gray-900">{totalResults}</span>{" "}
              results in <span className="font-semibold">{searchTime.toFixed(2)}s</span>
            </p>
          </div>
        )}

        {/* AI Summary */}
        {aiSummary && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">AI Summary</h3>
            <p className="text-blue-800">{aiSummary.summary}</p>
            <div className="mt-4 flex items-center gap-4 text-sm text-blue-700">
              <span>Sources: {aiSummary.sources_count}</span>
              <span>Confidence: {aiSummary.confidence}</span>
            </div>
          </div>
        )}

        {/* Results List */}
        <div className="space-y-4">
          {searchResults.map((result) => {
            const sourceConfig = SOURCE_CONFIG[result.source_type as keyof typeof SOURCE_CONFIG];

            return (
              <div
                key={result.document_id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${sourceConfig?.color || "text-gray-600 bg-gray-50"}`}
                    >
                      {sourceConfig?.icon} {sourceConfig?.name || result.source_type}
                    </span>
                    <span className="text-sm text-gray-500 flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {formatDate(result.created_at)}
                    </span>
                  </div>
                  <div className="text-sm font-medium text-green-600">
                    {formatScore(result.score)} match
                  </div>
                </div>

                {/* Title */}
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {result.title}
                </h3>

                {/* Preview */}
                <p className="text-gray-600 mb-4 line-clamp-3">
                  {result.content_preview}
                </p>

                {/* Footer */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      Chunk {result.chunk_index + 1}
                    </span>
                    {result.metadata?.author && (
                      <span>by {result.metadata.author}</span>
                    )}
                  </div>
                  {result.url && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      Open in {sourceConfig?.name}
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* No Results */}
        {!searchMutation.isPending &&
          !searchWithSummaryMutation.isPending &&
          searchResults.length === 0 &&
          query && (
            <div className="text-center py-12">
              <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
              <p className="text-gray-600">
                Try adjusting your search query or filters
              </p>
            </div>
          )}

        {/* Empty State */}
        {!query && (
          <div className="text-center py-12">
            <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Start searching your data
            </h3>
            <p className="text-gray-600">
              Enter a query above to search across all your connected data sources
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
