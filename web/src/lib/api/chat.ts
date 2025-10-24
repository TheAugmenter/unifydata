/**
 * Chat API Client
 */

import { api } from "./client";

export interface CreateConversationRequest {
  title?: string;
  model?: string;
}

export interface Conversation {
  id: string;
  title: string;
  model: string;
  temperature: number;
  message_count: number;
  total_tokens: number;
  is_archived: boolean;
  last_message_at: string | null;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  model: string | null;
  tokens_input: number | null;
  tokens_output: number | null;
  context_documents: string[] | null;
  thumbs_up: boolean | null;
  created_at: string;
}

export interface AskQuestionRequest {
  question: string;
  search_limit?: number;
}

export interface AskQuestionResponse {
  answer: string;
  context_documents: any[];
  model: string;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  response_time_ms: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  max_tokens: number;
  cost_input_per_1m: number;
  cost_output_per_1m: number;
  best_for: string;
}

export const chatApi = {
  /**
   * Create a new conversation
   */
  async createConversation(data: CreateConversationRequest = {}): Promise<Conversation> {
    const response = await api.post("/chat/conversations", data);
    return response.data;
  },

  /**
   * List conversations
   */
  async listConversations(limit = 50, includeArchived = false): Promise<Conversation[]> {
    const response = await api.get("/chat/conversations", {
      params: { limit, include_archived: includeArchived },
    });
    return response.data;
  },

  /**
   * Get conversation by ID
   */
  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await api.get(`/chat/conversations/${conversationId}`);
    return response.data;
  },

  /**
   * Delete conversation
   */
  async deleteConversation(conversationId: string): Promise<void> {
    await api.delete(`/chat/conversations/${conversationId}`);
  },

  /**
   * Archive conversation
   */
  async archiveConversation(conversationId: string): Promise<void> {
    await api.post(`/chat/conversations/${conversationId}/archive`);
  },

  /**
   * Get messages for a conversation
   */
  async getMessages(conversationId: string, limit?: number): Promise<Message[]> {
    const response = await api.get(`/chat/conversations/${conversationId}/messages`, {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Ask a question
   */
  async askQuestion(
    conversationId: string,
    data: AskQuestionRequest
  ): Promise<AskQuestionResponse> {
    const response = await api.post(
      `/chat/conversations/${conversationId}/messages`,
      data
    );
    return response.data;
  },

  /**
   * Update message feedback
   */
  async updateFeedback(
    messageId: string,
    thumbsUp: boolean | null,
    feedbackText?: string
  ): Promise<void> {
    await api.put(`/chat/messages/${messageId}/feedback`, {
      thumbs_up: thumbsUp,
      feedback_text: feedbackText,
    });
  },

  /**
   * List available AI models
   */
  async listModels(): Promise<ModelInfo[]> {
    const response = await api.get("/chat/models");
    return response.data;
  },
};
