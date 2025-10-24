/**
 * React Query hooks for Chat
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { chatApi, CreateConversationRequest, AskQuestionRequest } from "@/lib/api/chat";

/**
 * Hook for listing conversations
 */
export function useConversations(limit = 50, includeArchived = false) {
  return useQuery({
    queryKey: ["conversations", limit, includeArchived],
    queryFn: () => chatApi.listConversations(limit, includeArchived),
  });
}

/**
 * Hook for getting a single conversation
 */
export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => chatApi.getConversation(conversationId!),
    enabled: !!conversationId,
  });
}

/**
 * Hook for getting messages in a conversation
 */
export function useMessages(conversationId: string | null, limit?: number) {
  return useQuery({
    queryKey: ["messages", conversationId, limit],
    queryFn: () => chatApi.getMessages(conversationId!, limit),
    enabled: !!conversationId,
    refetchInterval: false, // Don't auto-refetch, we'll update manually
  });
}

/**
 * Hook for creating a conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateConversationRequest) => chatApi.createConversation(data),
    onSuccess: () => {
      // Invalidate conversations list
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

/**
 * Hook for asking a question
 */
export function useAskQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      conversationId,
      data,
    }: {
      conversationId: string;
      data: AskQuestionRequest;
    }) => chatApi.askQuestion(conversationId, data),
    onSuccess: (_, variables) => {
      // Invalidate messages for this conversation
      queryClient.invalidateQueries({ queryKey: ["messages", variables.conversationId] });
      // Invalidate conversations list (to update message count)
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

/**
 * Hook for deleting a conversation
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conversationId: string) => chatApi.deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

/**
 * Hook for archiving a conversation
 */
export function useArchiveConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conversationId: string) => chatApi.archiveConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

/**
 * Hook for updating message feedback
 */
export function useUpdateFeedback() {
  return useMutation({
    mutationFn: ({
      messageId,
      thumbsUp,
      feedbackText,
    }: {
      messageId: string;
      thumbsUp: boolean | null;
      feedbackText?: string;
    }) => chatApi.updateFeedback(messageId, thumbsUp, feedbackText),
  });
}

/**
 * Hook for listing available AI models
 */
export function useModels() {
  return useQuery({
    queryKey: ["chat-models"],
    queryFn: () => chatApi.listModels(),
    staleTime: Infinity, // Models don't change
  });
}
