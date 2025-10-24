"""
Vector Embeddings Service
Supports OpenAI and Anthropic models
"""
import logging
from typing import List, Dict, Any
import asyncio

from openai import AsyncOpenAI
import tiktoken

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings"""

    # Model configurations
    MODELS = {
        "openai-ada-002": {
            "provider": "openai",
            "model": "text-embedding-ada-002",
            "dimensions": 1536,
            "max_tokens": 8191,
            "encoding": "cl100k_base",
        },
        "openai-3-small": {
            "provider": "openai",
            "model": "text-embedding-3-small",
            "dimensions": 1536,
            "max_tokens": 8191,
            "encoding": "cl100k_base",
        },
        "openai-3-large": {
            "provider": "openai",
            "model": "text-embedding-3-large",
            "dimensions": 3072,
            "max_tokens": 8191,
            "encoding": "cl100k_base",
        },
    }

    # Default model
    DEFAULT_MODEL = "openai-ada-002"

    def __init__(self):
        """Initialize embeddings service"""
        self.logger = logger

        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Token encoders cache
        self.encoders: Dict[str, Any] = {}

    async def create_embedding(
        self,
        text: str,
        model: str = DEFAULT_MODEL,
    ) -> Dict[str, Any]:
        """
        Create embedding for a single text

        Args:
            text: Text to embed
            model: Model to use (default: openai-ada-002)

        Returns:
            Dict with embedding vector and metadata
        """
        # Get model config
        if model not in self.MODELS:
            raise ValueError(f"Unsupported model: {model}")

        model_config = self.MODELS[model]

        # Truncate text if needed
        truncated_text = await self._truncate_text(text, model_config)

        # Create embedding based on provider
        if model_config["provider"] == "openai":
            embedding = await self._create_openai_embedding(
                truncated_text,
                model_config["model"]
            )
        else:
            raise ValueError(f"Unsupported provider: {model_config['provider']}")

        return {
            "embedding": embedding,
            "model": model,
            "dimensions": len(embedding),
            "text_length": len(text),
            "truncated": len(text) != len(truncated_text),
        }

    async def create_embeddings_batch(
        self,
        texts: List[str],
        model: str = DEFAULT_MODEL,
        batch_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Create embeddings for multiple texts in batches

        Args:
            texts: List of texts to embed
            model: Model to use
            batch_size: Number of texts per batch

        Returns:
            List of embedding results
        """
        # Get model config
        if model not in self.MODELS:
            raise ValueError(f"Unsupported model: {model}")

        model_config = self.MODELS[model]

        # Process in batches
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Truncate texts
            truncated_batch = []
            for text in batch:
                truncated = await self._truncate_text(text, model_config)
                truncated_batch.append(truncated)

            # Create embeddings
            if model_config["provider"] == "openai":
                embeddings = await self._create_openai_embeddings_batch(
                    truncated_batch,
                    model_config["model"]
                )
            else:
                raise ValueError(f"Unsupported provider: {model_config['provider']}")

            # Format results
            for j, embedding in enumerate(embeddings):
                original_text = batch[j]
                results.append({
                    "embedding": embedding,
                    "model": model,
                    "dimensions": len(embedding),
                    "text_length": len(original_text),
                    "truncated": len(original_text) != len(truncated_batch[j]),
                })

            # Log progress
            self.logger.info(
                f"Created embeddings for batch {i // batch_size + 1} "
                f"({len(results)}/{len(texts)} total)"
            )

        return results

    async def _create_openai_embedding(self, text: str, model: str) -> List[float]:
        """Create embedding using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                input=text,
                model=model,
            )

            return response.data[0].embedding

        except Exception as e:
            self.logger.error(f"Error creating OpenAI embedding: {str(e)}", exc_info=True)
            raise

    async def _create_openai_embeddings_batch(
        self,
        texts: List[str],
        model: str
    ) -> List[List[float]]:
        """Create embeddings for batch using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                input=texts,
                model=model,
            )

            # Sort by index to maintain order
            sorted_embeddings = sorted(response.data, key=lambda x: x.index)

            return [item.embedding for item in sorted_embeddings]

        except Exception as e:
            self.logger.error(f"Error creating OpenAI embeddings batch: {str(e)}", exc_info=True)
            raise

    async def _truncate_text(self, text: str, model_config: Dict[str, Any]) -> str:
        """Truncate text to fit model's token limit"""
        # Get or create encoder
        encoding_name = model_config["encoding"]
        if encoding_name not in self.encoders:
            self.encoders[encoding_name] = tiktoken.get_encoding(encoding_name)

        encoder = self.encoders[encoding_name]

        # Count tokens
        tokens = encoder.encode(text)
        max_tokens = model_config["max_tokens"]

        # Truncate if needed
        if len(tokens) > max_tokens:
            self.logger.warning(
                f"Text exceeds max tokens ({len(tokens)} > {max_tokens}), truncating"
            )
            truncated_tokens = tokens[:max_tokens]
            return encoder.decode(truncated_tokens)

        return text

    def get_model_info(self, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
        """Get information about a model"""
        if model not in self.MODELS:
            raise ValueError(f"Unsupported model: {model}")

        return self.MODELS[model].copy()

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        return [
            {
                "name": name,
                **config
            }
            for name, config in self.MODELS.items()
        ]


# Create singleton instance
embeddings_service = EmbeddingsService()
