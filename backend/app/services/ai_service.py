"""
AI Service - Q&A with Anthropic Claude
"""
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime
import asyncio

from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered Q&A using Anthropic Claude"""

    # Model configurations
    MODELS = {
        "claude-3-5-sonnet-20241022": {
            "name": "Claude 3.5 Sonnet",
            "max_tokens": 200000,
            "cost_input_per_1m": 3.00,
            "cost_output_per_1m": 15.00,
            "best_for": "Most intelligent model, best for complex tasks",
        },
        "claude-3-5-haiku-20241022": {
            "name": "Claude 3.5 Haiku",
            "max_tokens": 200000,
            "cost_input_per_1m": 0.80,
            "cost_output_per_1m": 4.00,
            "best_for": "Fastest model, best for simple tasks",
        },
        "claude-3-opus-20240229": {
            "name": "Claude 3 Opus",
            "max_tokens": 200000,
            "cost_input_per_1m": 15.00,
            "cost_output_per_1m": 75.00,
            "best_for": "Most powerful model, best for very complex tasks",
        },
    }

    # Default model
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    # System prompt template
    SYSTEM_PROMPT = """You are an AI assistant with access to the user's connected data sources including Salesforce, Slack, Google Drive, Gmail, and Notion.

Your role is to help users find information across their data sources and answer questions based on the provided context.

Guidelines:
- Always base your answers on the provided context documents
- If the context doesn't contain enough information, say so clearly
- Cite specific sources when possible (mention the document title or source)
- Be concise but thorough
- If asked about something not in the context, explain that you can only answer based on available data
- Format your responses in markdown for better readability
- Use bullet points, numbered lists, and formatting to make information clear

Current date: {current_date}
"""

    def __init__(self):
        """Initialize AI service"""
        self.logger = logger
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        context_documents: List[Dict[str, Any]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Generate AI response (non-streaming)

        Args:
            messages: List of conversation messages [{"role": "user|assistant", "content": "..."}]
            context_documents: List of relevant documents for context
            model: AI model to use
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with response and metadata
        """
        start_time = datetime.utcnow()

        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(context_documents)

            # Call Claude API
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
            )

            # Calculate response time
            response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Extract response text
            response_text = response.content[0].text if response.content else ""

            # Calculate cost
            cost_usd = self._calculate_cost(
                model=model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            return {
                "content": response_text,
                "model": model,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "cost_usd": cost_usd,
                "response_time_ms": response_time_ms,
                "stop_reason": response.stop_reason,
            }

        except Exception as e:
            self.logger.error(f"Error in AI chat: {str(e)}", exc_info=True)
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        context_documents: List[Dict[str, Any]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate AI response with streaming

        Args:
            messages: List of conversation messages
            context_documents: List of relevant documents for context
            model: AI model to use
            temperature: Creativity level
            max_tokens: Maximum tokens to generate

        Yields:
            Dict with streaming events
        """
        start_time = datetime.utcnow()

        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(context_documents)

            # Stream from Claude API
            async with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
            ) as stream:

                # Yield stream events
                async for event in stream:
                    if event.type == "content_block_delta":
                        # Text chunk
                        if hasattr(event.delta, "text"):
                            yield {
                                "type": "content",
                                "content": event.delta.text,
                            }

                    elif event.type == "message_start":
                        # Message started
                        yield {
                            "type": "start",
                            "model": model,
                        }

                    elif event.type == "message_stop":
                        # Message completed
                        response_time_ms = int(
                            (datetime.utcnow() - start_time).total_seconds() * 1000
                        )
                        yield {
                            "type": "end",
                            "response_time_ms": response_time_ms,
                        }

                # Get final message for usage stats
                final_message = await stream.get_final_message()

                # Calculate cost
                cost_usd = self._calculate_cost(
                    model=model,
                    input_tokens=final_message.usage.input_tokens,
                    output_tokens=final_message.usage.output_tokens,
                )

                # Yield final metadata
                yield {
                    "type": "metadata",
                    "tokens_input": final_message.usage.input_tokens,
                    "tokens_output": final_message.usage.output_tokens,
                    "cost_usd": cost_usd,
                    "stop_reason": final_message.stop_reason,
                }

        except Exception as e:
            self.logger.error(f"Error in AI chat stream: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
            }

    def _build_system_prompt(self, context_documents: List[Dict[str, Any]]) -> str:
        """
        Build system prompt with context from documents

        Args:
            context_documents: List of relevant documents

        Returns:
            System prompt with context
        """
        # Start with base system prompt
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        prompt = self.SYSTEM_PROMPT.format(current_date=current_date)

        # Add context documents
        if context_documents:
            prompt += "\n\n## Available Context\n\n"
            prompt += "Here are the relevant documents from the user's data sources:\n\n"

            for i, doc in enumerate(context_documents, 1):
                source_type = doc.get("source_type", "unknown")
                title = doc.get("title", "Untitled")
                content = doc.get("content", "")
                url = doc.get("url", "")

                prompt += f"### Document {i}: {title}\n"
                prompt += f"**Source:** {source_type.replace('_', ' ').title()}\n"
                if url:
                    prompt += f"**URL:** {url}\n"
                prompt += f"\n{content}\n\n"
                prompt += "---\n\n"

        return prompt

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Calculate cost for API usage

        Args:
            model: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        if model not in self.MODELS:
            return 0.0

        model_config = self.MODELS[model]

        input_cost = (input_tokens / 1_000_000) * model_config["cost_input_per_1m"]
        output_cost = (output_tokens / 1_000_000) * model_config["cost_output_per_1m"]

        return round(input_cost + output_cost, 6)

    def get_model_info(self, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
        """Get information about a model"""
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}")

        return self.MODELS[model].copy()

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        return [
            {
                "id": model_id,
                **config
            }
            for model_id, config in self.MODELS.items()
        ]


# Create singleton instance
ai_service = AIService()
