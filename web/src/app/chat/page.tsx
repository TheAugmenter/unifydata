"use client";

import { useState, useEffect, useRef } from "react";
import {
  MessageCircle,
  Plus,
  Send,
  ThumbsUp,
  ThumbsDown,
  Trash2,
  Archive,
  FileText,
  Loader2,
} from "lucide-react";
import {
  useConversations,
  useMessages,
  useCreateConversation,
  useAskQuestion,
  useDeleteConversation,
  useArchiveConversation,
  useUpdateFeedback,
  useModels,
} from "@/hooks/use-chat";
import { toast } from "sonner";
import { format } from "date-fns";

export default function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Queries
  const { data: conversations, isLoading: loadingConversations } = useConversations();
  const { data: messages, isLoading: loadingMessages } = useMessages(selectedConversationId);
  const { data: models } = useModels();

  // Mutations
  const createConversation = useCreateConversation();
  const askQuestion = useAskQuestion();
  const deleteConversation = useDeleteConversation();
  const archiveConversation = useArchiveConversation();
  const updateFeedback = useUpdateFeedback();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Select first conversation on load
  useEffect(() => {
    if (conversations && conversations.length > 0 && !selectedConversationId) {
      setSelectedConversationId(conversations[0].id);
    }
  }, [conversations, selectedConversationId]);

  const handleNewConversation = async () => {
    try {
      const newConv = await createConversation.mutateAsync({
        title: "New Conversation",
      });
      setSelectedConversationId(newConv.id);
      toast.success("New conversation created");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to create conversation");
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim() || !selectedConversationId) return;

    const questionText = question;
    setQuestion(""); // Clear input immediately

    try {
      await askQuestion.mutateAsync({
        conversationId: selectedConversationId,
        data: { question: questionText },
      });
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to send message");
      setQuestion(questionText); // Restore question on error
    }
  };

  const handleDelete = async (conversationId: string) => {
    if (!confirm("Are you sure you want to delete this conversation?")) return;

    try {
      await deleteConversation.mutateAsync(conversationId);
      if (selectedConversationId === conversationId) {
        setSelectedConversationId(null);
      }
      toast.success("Conversation deleted");
    } catch (error: any) {
      toast.error("Failed to delete conversation");
    }
  };

  const handleArchive = async (conversationId: string) => {
    try {
      await archiveConversation.mutateAsync(conversationId);
      toast.success("Conversation archived");
    } catch (error: any) {
      toast.error("Failed to archive conversation");
    }
  };

  const handleFeedback = async (messageId: string, thumbsUp: boolean) => {
    try {
      await updateFeedback.mutateAsync({ messageId, thumbsUp });
    } catch (error: any) {
      toast.error("Failed to update feedback");
    }
  };

  const selectedConversation = conversations?.find((c) => c.id === selectedConversationId);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - Conversations */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewConversation}
            disabled={createConversation.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Plus className="w-5 h-5" />
            New Chat
          </button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {loadingConversations ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : conversations && conversations.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConversationId(conv.id)}
                  className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                    selectedConversationId === conv.id ? "bg-blue-50 border-l-4 border-blue-600" : ""
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">{conv.title}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {conv.message_count} messages
                      </p>
                      {conv.last_message_at && (
                        <p className="text-xs text-gray-400 mt-1">
                          {format(new Date(conv.last_message_at), "MMM d, h:mm a")}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-1 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleArchive(conv.id);
                        }}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                        title="Archive"
                      >
                        <Archive className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(conv.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 rounded"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <MessageCircle className="w-12 h-12 text-gray-300 mb-4" />
              <p className="text-gray-500">No conversations yet</p>
              <p className="text-sm text-gray-400 mt-1">Create a new chat to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedConversationId ? (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
              <h2 className="text-xl font-semibold text-gray-900">
                {selectedConversation?.title || "Chat"}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {selectedConversation?.model} · {selectedConversation?.message_count} messages
              </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
              {loadingMessages ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                </div>
              ) : messages && messages.length > 0 ? (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-3xl rounded-lg px-4 py-3 ${
                        message.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-white border border-gray-200"
                      }`}
                    >
                      <div className="prose prose-sm max-w-none">
                        {message.role === "assistant" ? (
                          <div
                            className="text-gray-800"
                            dangerouslySetInnerHTML={{
                              __html: message.content.replace(/\n/g, "<br />"),
                            }}
                          />
                        ) : (
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        )}
                      </div>

                      {/* Assistant message footer */}
                      {message.role === "assistant" && (
                        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            {message.tokens_input && message.tokens_output && (
                              <span>
                                {message.tokens_input + message.tokens_output} tokens
                              </span>
                            )}
                            {message.context_documents && message.context_documents.length > 0 && (
                              <span className="flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                {message.context_documents.length} sources
                              </span>
                            )}
                          </div>

                          {/* Feedback buttons */}
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleFeedback(message.id, true)}
                              className={`p-1 rounded transition-colors ${
                                message.thumbs_up === true
                                  ? "text-green-600 bg-green-50"
                                  : "text-gray-400 hover:text-green-600"
                              }`}
                              title="Helpful"
                            >
                              <ThumbsUp className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleFeedback(message.id, false)}
                              className={`p-1 rounded transition-colors ${
                                message.thumbs_up === false
                                  ? "text-red-600 bg-red-50"
                                  : "text-gray-400 hover:text-red-600"
                              }`}
                              title="Not helpful"
                            >
                              <ThumbsDown className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <MessageCircle className="w-16 h-16 text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Start a conversation
                  </h3>
                  <p className="text-gray-500 max-w-md">
                    Ask a question to search across your connected data sources and get AI-powered answers.
                  </p>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="bg-white border-t border-gray-200 px-6 py-4">
              <form onSubmit={handleSendMessage} className="flex gap-4">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question..."
                  disabled={askQuestion.isPending}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                  type="submit"
                  disabled={!question.trim() || askQuestion.isPending}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {askQuestion.isPending ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Thinking...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Send
                    </>
                  )}
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <MessageCircle className="w-20 h-20 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-gray-900 mb-2">
                Select or create a conversation
              </h3>
              <p className="text-gray-500">
                Choose a conversation from the sidebar or start a new one
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
