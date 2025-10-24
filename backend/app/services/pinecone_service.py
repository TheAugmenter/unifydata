"""
Pinecone Vector Storage Service
"""
import logging
from typing import List, Dict, Any, Optional
import uuid

from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings

logger = logging.getLogger(__name__)


class PineconeService:
    """Service for managing vectors in Pinecone"""

    def __init__(self):
        """Initialize Pinecone client"""
        self.logger = logger
        self.pc = None
        self.index_name = settings.PINECONE_INDEX_NAME
        self.index = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Pinecone client"""
        if self._initialized:
            return

        try:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self._init_index()
            self._initialized = True
        except Exception as e:
            self.logger.error(f"Failed to initialize Pinecone: {str(e)}")
            raise

    def _init_index(self):
        """Initialize or create Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes().names()

            if self.index_name not in existing_indexes:
                self.logger.info(f"Creating Pinecone index: {self.index_name}")

                # Create index with OpenAI ada-002 dimensions (1536)
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI text-embedding-ada-002
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )

                self.logger.info(f"Pinecone index created: {self.index_name}")

            # Connect to index
            self.index = self.pc.Index(self.index_name)
            self.logger.info(f"Connected to Pinecone index: {self.index_name}")

        except Exception as e:
            self.logger.error(f"Error initializing Pinecone: {str(e)}", exc_info=True)
            raise

    async def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upsert vectors to Pinecone

        Args:
            vectors: List of vectors with format:
                [
                    {
                        "id": "unique-id",
                        "values": [0.1, 0.2, ...],  # 1536 dimensions for ada-002
                        "metadata": {
                            "document_id": "uuid",
                            "org_id": "uuid",
                            "source_type": "salesforce",
                            "title": "Document title",
                            "content": "Text content (for context)",
                            "url": "https://...",
                            ...
                        }
                    },
                    ...
                ]
            namespace: Optional namespace for multi-tenancy

        Returns:
            Dict with upsert results
        """
        self._ensure_initialized()
        try:
            if not vectors:
                return {"upserted_count": 0}

            # Format vectors for Pinecone
            formatted_vectors = []
            for vec in vectors:
                formatted_vectors.append({
                    "id": vec["id"],
                    "values": vec["values"],
                    "metadata": vec.get("metadata", {}),
                })

            # Upsert to Pinecone
            result = self.index.upsert(
                vectors=formatted_vectors,
                namespace=namespace or ""
            )

            self.logger.info(
                f"Upserted {result.upserted_count} vectors to Pinecone "
                f"(namespace: {namespace or 'default'})"
            )

            return {
                "upserted_count": result.upserted_count,
            }

        except Exception as e:
            self.logger.error(f"Error upserting vectors: {str(e)}", exc_info=True)
            raise

    async def query(
        self,
        query_vector: List[float],
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for similar vectors

        Args:
            query_vector: Query embedding vector (1536 dimensions)
            top_k: Number of results to return
            namespace: Optional namespace for multi-tenancy
            filter_metadata: Optional metadata filters
            include_metadata: Whether to include metadata in results

        Returns:
            List of matches with scores and metadata
        """
        self._ensure_initialized()
        try:
            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace or "",
                filter=filter_metadata,
                include_metadata=include_metadata,
            )

            # Format results
            matches = []
            for match in results.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {},
                })

            self.logger.info(
                f"Found {len(matches)} matches in Pinecone "
                f"(namespace: {namespace or 'default'})"
            )

            return matches

        except Exception as e:
            self.logger.error(f"Error querying Pinecone: {str(e)}", exc_info=True)
            raise

    async def delete_vectors(
        self,
        vector_ids: List[str],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Delete vectors from Pinecone

        Args:
            vector_ids: List of vector IDs to delete
            namespace: Optional namespace

        Returns:
            Dict with deletion results
        """
        self._ensure_initialized()
        try:
            if not vector_ids:
                return {"deleted_count": 0}

            # Delete from Pinecone
            self.index.delete(
                ids=vector_ids,
                namespace=namespace or ""
            )

            self.logger.info(
                f"Deleted {len(vector_ids)} vectors from Pinecone "
                f"(namespace: {namespace or 'default'})"
            )

            return {"deleted_count": len(vector_ids)}

        except Exception as e:
            self.logger.error(f"Error deleting vectors: {str(e)}", exc_info=True)
            raise

    async def delete_by_filter(
        self,
        filter_metadata: Dict[str, Any],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Delete vectors by metadata filter

        Args:
            filter_metadata: Metadata filter for deletion
            namespace: Optional namespace

        Returns:
            Dict with deletion results
        """
        self._ensure_initialized()
        try:
            # Delete by filter
            self.index.delete(
                filter=filter_metadata,
                namespace=namespace or ""
            )

            self.logger.info(
                f"Deleted vectors by filter from Pinecone "
                f"(namespace: {namespace or 'default'})"
            )

            return {"status": "deleted"}

        except Exception as e:
            self.logger.error(f"Error deleting by filter: {str(e)}", exc_info=True)
            raise

    async def get_index_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get index statistics

        Args:
            namespace: Optional namespace

        Returns:
            Dict with index stats
        """
        self._ensure_initialized()
        try:
            stats = self.index.describe_index_stats()

            namespace_stats = None
            if namespace and namespace in stats.namespaces:
                namespace_stats = stats.namespaces[namespace]

            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespace_count": len(stats.namespaces),
                "namespace_stats": namespace_stats,
            }

        except Exception as e:
            self.logger.error(f"Error getting index stats: {str(e)}", exc_info=True)
            raise


# Create singleton instance
pinecone_service = PineconeService()
