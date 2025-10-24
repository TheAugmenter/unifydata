/**
 * React Query hooks for Search
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { searchApi, SearchRequest } from "@/lib/api/search";

/**
 * Hook for performing search
 */
export function useSearch() {
  return useMutation({
    mutationFn: (request: SearchRequest) => searchApi.search(request),
  });
}

/**
 * Hook for search with AI summary
 */
export function useSearchWithSummary() {
  return useMutation({
    mutationFn: (request: SearchRequest) => searchApi.searchWithSummary(request),
  });
}

/**
 * Hook for getting search suggestions
 */
export function useSearchSuggestions(q: string, enabled = false) {
  return useQuery({
    queryKey: ["search-suggestions", q],
    queryFn: () => searchApi.getSuggestions(q),
    enabled: enabled && q.length >= 2,
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook for getting related documents
 */
export function useRelatedDocuments(documentId: string | null) {
  return useQuery({
    queryKey: ["related-documents", documentId],
    queryFn: () => searchApi.getRelatedDocuments(documentId!),
    enabled: !!documentId,
  });
}
