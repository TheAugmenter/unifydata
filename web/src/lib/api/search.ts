/**
 * Search API Client
 */

import { api } from "./client";

export interface SearchRequest {
  query: string;
  limit?: number;
  source_types?: string[];
  min_score?: number;
}

export interface SearchResultItem {
  document_id: string;
  title: string;
  content_preview: string;
  source_type: string;
  url: string | null;
  score: number;
  chunk_index: number;
  created_at: string;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total_results: number;
  search_time_seconds: number;
  filters: {
    source_types?: string[];
    min_score: number;
  };
}

export interface SearchWithSummaryResponse extends SearchResponse {
  ai_summary: {
    summary: string;
    sources_count: number;
    confidence: string;
  };
}

export const searchApi = {
  /**
   * Perform semantic search
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await api.post("/search/search", request);
    return response.data;
  },

  /**
   * Perform search with AI summary
   */
  async searchWithSummary(request: SearchRequest): Promise<SearchWithSummaryResponse> {
    const response = await api.post("/search/search/with-summary", request);
    return response.data;
  },

  /**
   * Get search suggestions
   */
  async getSuggestions(q: string, limit = 5): Promise<string[]> {
    const response = await api.get("/search/search/suggestions", {
      params: { q, limit },
    });
    return response.data.suggestions;
  },

  /**
   * Get related documents
   */
  async getRelatedDocuments(documentId: string, limit = 5): Promise<SearchResultItem[]> {
    const response = await api.get(`/search/documents/${documentId}/related`, {
      params: { limit },
    });
    return response.data.related_documents;
  },
};
