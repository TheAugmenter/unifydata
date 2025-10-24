"""
Data Sync Service
Orchestrates document fetching, parsing, embedding, and storage
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import DataSource, Document, DocumentChunk, SyncLog
from app.connectors.salesforce import SalesforceConnector
from app.connectors.slack import SlackConnector
from app.connectors.google import GoogleConnector
from app.connectors.notion import NotionConnector
from app.services.document_parser import document_parser_service
from app.services.embeddings import embeddings_service
from app.services.pinecone_service import pinecone_service

logger = logging.getLogger(__name__)


class DataSyncService:
    """Service for syncing data from connected sources"""

    # Connector classes (will be instantiated per request)
    CONNECTORS = {
        "salesforce": SalesforceConnector,
        "slack": SlackConnector,
        "google_drive": GoogleConnector,
        "gmail": GoogleConnector,
        "notion": NotionConnector,
    }

    def __init__(self):
        """Initialize data sync service"""
        self.logger = logger

    async def sync_data_source(
        self,
        db: AsyncSession,
        data_source_id: uuid.UUID,
        sync_type: str = "manual",
    ) -> Dict[str, Any]:
        """
        Sync a single data source

        Args:
            db: Database session
            data_source_id: ID of data source to sync
            sync_type: Type of sync (manual, automatic, initial)

        Returns:
            Dict with sync results
        """
        self.logger.info(f"Starting sync for data source: {data_source_id}")

        # Get data source
        result = await db.execute(
            select(DataSource).where(DataSource.id == data_source_id)
        )
        data_source = result.scalar_one_or_none()

        if not data_source:
            raise ValueError(f"Data source not found: {data_source_id}")

        if not data_source.is_active:
            raise ValueError(f"Data source is not active: {data_source_id}")

        # Create sync log
        sync_log = SyncLog(
            data_source_id=data_source_id,
            status="in_progress",
            sync_type=sync_type,
            started_at=datetime.utcnow(),
        )
        db.add(sync_log)
        await db.commit()
        await db.refresh(sync_log)

        try:
            # Update data source status
            await db.execute(
                update(DataSource)
                .where(DataSource.id == data_source_id)
                .values(
                    status="syncing",
                    last_sync_status="in_progress",
                )
            )
            await db.commit()

            # Get connector
            connector = self.CONNECTORS.get(data_source.source_type)
            if not connector:
                raise ValueError(f"No connector for source type: {data_source.source_type}")

            # Fetch documents from source
            self.logger.info(f"Fetching documents from {data_source.source_type}")
            documents = await self._fetch_documents(
                connector=connector,
                data_source=data_source,
            )

            self.logger.info(f"Fetched {len(documents)} documents from source")

            # Process each document
            stats = {
                "processed": 0,
                "added": 0,
                "updated": 0,
                "failed": 0,
            }

            for doc_data in documents:
                try:
                    result = await self._process_document(
                        db=db,
                        data_source=data_source,
                        doc_data=doc_data,
                    )

                    if result["action"] == "created":
                        stats["added"] += 1
                    elif result["action"] == "updated":
                        stats["updated"] += 1

                    stats["processed"] += 1

                except Exception as e:
                    self.logger.error(
                        f"Error processing document {doc_data.get('id')}: {str(e)}",
                        exc_info=True
                    )
                    stats["failed"] += 1

            # Update sync log
            sync_log.status = "success"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int(
                (sync_log.completed_at - sync_log.started_at).total_seconds()
            )
            sync_log.documents_processed = stats["processed"]
            sync_log.documents_added = stats["added"]
            sync_log.documents_updated = stats["updated"]

            # Update data source
            await db.execute(
                update(DataSource)
                .where(DataSource.id == data_source_id)
                .values(
                    status="connected",
                    last_sync_status="success",
                    last_sync_at=datetime.utcnow(),
                    last_sync_error=None,
                    next_sync_at=datetime.utcnow() + timedelta(seconds=data_source.sync_frequency),
                    total_documents=data_source.total_documents + stats["added"],
                    total_sync_count=data_source.total_sync_count + 1,
                )
            )

            await db.commit()

            self.logger.info(
                f"Sync completed for data source {data_source_id}: "
                f"{stats['processed']} processed, {stats['added']} added, "
                f"{stats['updated']} updated, {stats['failed']} failed"
            )

            return {
                "sync_log_id": sync_log.id,
                "status": "success",
                "stats": stats,
            }

        except Exception as e:
            self.logger.error(f"Sync failed for data source {data_source_id}: {str(e)}", exc_info=True)

            # Update sync log
            sync_log.status = "failed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int(
                (sync_log.completed_at - sync_log.started_at).total_seconds()
            )
            sync_log.error_message = str(e)

            # Update data source
            await db.execute(
                update(DataSource)
                .where(DataSource.id == data_source_id)
                .values(
                    status="error",
                    last_sync_status="failed",
                    last_sync_error=str(e),
                    failed_sync_count=data_source.failed_sync_count + 1,
                )
            )

            await db.commit()

            raise

    async def _fetch_documents(
        self,
        connector: Any,
        data_source: DataSource,
    ) -> List[Dict[str, Any]]:
        """
        Fetch documents from data source

        Returns:
            List of document data dicts
        """
        # Each connector should implement a fetch_documents method
        # For now, return empty list (to be implemented in each connector)

        # Example structure for each document:
        # {
        #     "id": "external-id",
        #     "title": "Document title",
        #     "content": "Document content (optional if has url/file)",
        #     "url": "https://...",
        #     "file_url": "https://download-url...",
        #     "content_type": "document|email|message|page|file",
        #     "mime_type": "application/pdf",
        #     "metadata": {
        #         "author": "...",
        #         "created_at": "...",
        #         "tags": [...],
        #         ...
        #     },
        #     "created_at": datetime,
        #     "updated_at": datetime,
        # }

        # TODO: Implement connector methods
        self.logger.warning(f"Fetch documents not yet implemented for {data_source.source_type}")
        return []

    async def _process_document(
        self,
        db: AsyncSession,
        data_source: DataSource,
        doc_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a single document: parse, chunk, embed, and store

        Args:
            db: Database session
            data_source: Data source
            doc_data: Document data from connector

        Returns:
            Dict with processing result
        """
        external_id = doc_data["id"]

        # Check if document already exists
        result = await db.execute(
            select(Document).where(
                Document.data_source_id == data_source.id,
                Document.external_id == external_id,
            )
        )
        existing_doc = result.scalar_one_or_none()

        # If exists and not updated, skip
        if existing_doc and doc_data.get("updated_at"):
            if existing_doc.source_updated_at and existing_doc.source_updated_at >= doc_data["updated_at"]:
                self.logger.debug(f"Document {external_id} not updated, skipping")
                return {"action": "skipped", "document_id": existing_doc.id}

        # Parse document content
        parsed_content = None
        if doc_data.get("content"):
            # Content is already text
            parsed_content = {
                "content": doc_data["content"],
                "word_count": len(doc_data["content"].split()),
                "char_count": len(doc_data["content"]),
            }
        elif doc_data.get("file_url"):
            # Download and parse file
            # TODO: Implement file download and parsing
            self.logger.warning("File download not yet implemented")
            return {"action": "skipped", "reason": "file_download_not_implemented"}

        if not parsed_content:
            self.logger.warning(f"No content for document {external_id}")
            return {"action": "skipped", "reason": "no_content"}

        # Create or update document
        if existing_doc:
            # Update existing document
            existing_doc.title = doc_data.get("title", "Untitled")
            existing_doc.content = parsed_content["content"]
            existing_doc.word_count = parsed_content.get("word_count")
            existing_doc.char_count = parsed_content.get("char_count")
            existing_doc.url = doc_data.get("url")
            existing_doc.source_metadata = doc_data.get("metadata", {})
            existing_doc.source_updated_at = doc_data.get("updated_at")
            existing_doc.parse_status = "completed"
            existing_doc.embedding_status = "pending"  # Re-embed on update
            existing_doc.updated_at = datetime.utcnow()

            document = existing_doc
            action = "updated"

        else:
            # Create new document
            document = Document(
                data_source_id=data_source.id,
                org_id=data_source.org_id,
                external_id=external_id,
                source_type=data_source.source_type,
                title=doc_data.get("title", "Untitled"),
                content=parsed_content["content"],
                content_type=doc_data.get("content_type", "document"),
                mime_type=doc_data.get("mime_type"),
                url=doc_data.get("url"),
                word_count=parsed_content.get("word_count"),
                char_count=parsed_content.get("char_count"),
                source_metadata=doc_data.get("metadata", {}),
                source_created_at=doc_data.get("created_at"),
                source_updated_at=doc_data.get("updated_at"),
                parse_status="completed",
                embedding_status="pending",
            )
            db.add(document)
            action = "created"

        await db.commit()
        await db.refresh(document)

        # Chunk the document
        chunks = document_parser_service.chunk_text(
            parsed_content["content"],
            chunk_size=1000,
            overlap=200,
        )

        # Delete old chunks if updating
        if action == "updated" and existing_doc:
            await db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            # TODO: Delete old chunks and vectors

        # Create chunks
        chunk_objects = []
        for chunk in chunks:
            chunk_obj = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk["index"],
                content=chunk["content"],
                char_count=chunk["char_count"],
                embedding_status="pending",
            )
            db.add(chunk_obj)
            chunk_objects.append(chunk_obj)

        await db.commit()

        # Create embeddings (async task would be better)
        try:
            await self._create_embeddings(db, document, chunk_objects)
        except Exception as e:
            self.logger.error(f"Error creating embeddings: {str(e)}", exc_info=True)
            document.embedding_status = "failed"
            await db.commit()

        return {
            "action": action,
            "document_id": document.id,
            "chunks": len(chunk_objects),
        }

    async def _create_embeddings(
        self,
        db: AsyncSession,
        document: Document,
        chunks: List[DocumentChunk],
    ):
        """Create embeddings for document chunks"""

        if not chunks:
            return

        # Get chunk texts
        texts = [chunk.content for chunk in chunks]

        # Create embeddings
        self.logger.info(f"Creating embeddings for {len(texts)} chunks")
        embeddings = await embeddings_service.create_embeddings_batch(texts)

        # Prepare vectors for Pinecone
        vectors = []
        for i, (chunk, embedding_data) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{document.id}_{chunk.chunk_index}"

            vectors.append({
                "id": vector_id,
                "values": embedding_data["embedding"],
                "metadata": {
                    "document_id": str(document.id),
                    "chunk_index": chunk.chunk_index,
                    "org_id": str(document.org_id),
                    "source_type": document.source_type,
                    "title": document.title,
                    "content": chunk.content[:500],  # First 500 chars for context
                    "url": document.url or "",
                    "created_at": document.created_at.isoformat(),
                },
            })

            # Update chunk
            chunk.vector_id = vector_id
            chunk.embedding_status = "completed"

        # Upsert to Pinecone
        namespace = str(document.org_id)  # Use org_id as namespace for multi-tenancy
        await pinecone_service.upsert_vectors(vectors, namespace=namespace)

        # Update document
        document.embedding_status = "completed"
        document.embedding_model = "openai-ada-002"
        document.embedding_created_at = datetime.utcnow()

        await db.commit()

        self.logger.info(f"Created and stored {len(vectors)} embeddings")


# Create singleton instance
data_sync_service = DataSyncService()
