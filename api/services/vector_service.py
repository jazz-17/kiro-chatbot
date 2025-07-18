"""
PostgreSQL Vector Database Service with pgvector support

This module implements the VectorDatabase interface using PostgreSQL with pgvector extension
for storing and searching document embeddings.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, and_
from sqlalchemy.orm import selectinload

from services.base import VectorDatabase
from database.models import DocumentChunkDB, DocumentDB
from models.document import DocumentChunk, DocumentChunkCreate
from database.base import async_session_maker

logger = logging.getLogger(__name__)


class PostgreSQLVectorDB(VectorDatabase):
    """PostgreSQL implementation of VectorDatabase interface using pgvector"""

    def __init__(self, embedding_dimension: int = 1536):
        """
        Initialize PostgreSQL Vector Database

        Args:
            embedding_dimension: Dimension of the embedding vectors (default: 1536 for OpenAI)
        """
        self.embedding_dimension = embedding_dimension

    async def store_embeddings(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Store multiple document chunks with their embeddings

        Args:
            documents: List of documents containing:
                - content: Text content of the chunk
                - embedding: Vector embedding as list of floats
                - document_id: UUID of the parent document
                - chunk_index: Index of the chunk within the document
                - metadata: Additional metadata dictionary

        Returns:
            List of chunk IDs that were created
        """
        async with async_session_maker() as session:
            try:
                chunk_ids = []

                for doc_data in documents:
                    # Validate embedding dimension
                    embedding = doc_data.get("embedding", [])
                    if len(embedding) != self.embedding_dimension:
                        raise ValueError(
                            f"Embedding dimension {len(embedding)} does not match "
                            f"expected dimension {self.embedding_dimension}"
                        )

                    # Create document chunk
                    chunk_db = DocumentChunkDB(
                        document_id=doc_data["document_id"],
                        content=doc_data["content"],
                        chunk_index=doc_data["chunk_index"],
                        embedding=embedding,
                        meta_data=doc_data.get("metadata", {}),
                    )

                    session.add(chunk_db)
                    await session.flush()  # Get the ID
                    chunk_ids.append(str(chunk_db.id))

                await session.commit()
                logger.info(f"Stored {len(chunk_ids)} document chunks")
                return chunk_ids

            except Exception as e:
                await session.rollback()
                logger.error(f"Error storing embeddings: {str(e)}")
                raise

    async def store_embedding(
        self, content: str, embedding: List[float], metadata: Dict[str, Any]
    ) -> str:
        """
        Store a single document chunk with its embedding

        Args:
            content: Text content of the chunk
            embedding: Vector embedding as list of floats
            metadata: Metadata including document_id, chunk_index, etc.

        Returns:
            ID of the created chunk
        """
        documents = [
            {
                "content": content,
                "embedding": embedding,
                "document_id": metadata["document_id"],
                "chunk_index": metadata.get("chunk_index", 0),
                "metadata": metadata,
            }
        ]

        chunk_ids = await self.store_embeddings(documents)
        return chunk_ids[0]

    async def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.7,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search against stored embeddings

        Args:
            query_embedding: Query vector embedding
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0-1, where 1 is identical)
            document_ids: Optional list of document IDs to filter by

        Returns:
            List of similar chunks with metadata and similarity scores
        """
        if len(query_embedding) != self.embedding_dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"expected dimension {self.embedding_dimension}"
            )

        async with async_session_maker() as session:
            try:
                # Build the similarity search query using cosine similarity
                # pgvector uses 1 - cosine_distance for cosine similarity
                query = (
                    select(
                        DocumentChunkDB.id,
                        DocumentChunkDB.content,
                        DocumentChunkDB.chunk_index,
                        DocumentChunkDB.meta_data,
                        DocumentChunkDB.document_id,
                        DocumentDB.filename,
                        DocumentDB.s3_key,
                        # Calculate cosine similarity (1 - cosine distance)
                        (
                            1
                            - func.cosine_distance(
                                DocumentChunkDB.embedding, query_embedding
                            )
                        ).label("similarity_score"),
                    )
                    .select_from(DocumentChunkDB.__table__.join(DocumentDB.__table__))
                    .where(
                        # Filter by similarity threshold
                        (
                            1
                            - func.cosine_distance(
                                DocumentChunkDB.embedding, query_embedding
                            )
                        )
                        >= threshold
                    )
                )

                # Add document ID filter if provided
                if document_ids:
                    query = query.where(DocumentChunkDB.document_id.in_(document_ids))

                # Order by similarity score descending and limit results
                query = query.order_by(
                    (
                        1
                        - func.cosine_distance(
                            DocumentChunkDB.embedding, query_embedding
                        )
                    ).desc()
                ).limit(limit)

                result = await session.execute(query)
                rows = result.fetchall()

                # Format results
                similar_chunks = []
                for row in rows:
                    chunk_data = {
                        "id": str(row.id),
                        "content": row.content,
                        "chunk_index": row.chunk_index,
                        "document_id": str(row.document_id),
                        "document_filename": row.filename,
                        "document_s3_key": row.s3_key,
                        "similarity_score": float(row.similarity_score),
                        "metadata": row.meta_data or {},
                    }
                    similar_chunks.append(chunk_data)

                logger.info(
                    f"Found {len(similar_chunks)} similar chunks with "
                    f"threshold >= {threshold}"
                )
                return similar_chunks

            except Exception as e:
                logger.error(f"Error performing similarity search: {str(e)}")
                raise

    async def delete_embedding(self, embedding_id: str) -> bool:
        """
        Delete a document chunk by ID

        Args:
            embedding_id: ID of the chunk to delete

        Returns:
            True if deleted successfully, False if not found
        """
        async with async_session_maker() as session:
            try:
                # Find the chunk
                query = select(DocumentChunkDB).where(
                    DocumentChunkDB.id == UUID(embedding_id)
                )
                result = await session.execute(query)
                chunk = result.scalar_one_or_none()

                if not chunk:
                    logger.warning(f"Chunk with ID {embedding_id} not found")
                    return False

                # Delete the chunk
                await session.delete(chunk)
                await session.commit()

                logger.info(f"Deleted chunk with ID {embedding_id}")
                return True

            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting embedding {embedding_id}: {str(e)}")
                raise

    async def delete_document_embeddings(self, document_id: UUID) -> int:
        """
        Delete all chunks for a specific document

        Args:
            document_id: ID of the document whose chunks to delete

        Returns:
            Number of chunks deleted
        """
        async with async_session_maker() as session:
            try:
                # Find all chunks for the document
                query = select(DocumentChunkDB).where(
                    DocumentChunkDB.document_id == document_id
                )
                result = await session.execute(query)
                chunks = result.scalars().all()

                # Delete all chunks
                for chunk in chunks:
                    await session.delete(chunk)

                await session.commit()

                logger.info(f"Deleted {len(chunks)} chunks for document {document_id}")
                return len(chunks)

            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting document embeddings: {str(e)}")
                raise

    async def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific chunk by ID

        Args:
            chunk_id: ID of the chunk to retrieve

        Returns:
            Chunk data or None if not found
        """
        async with async_session_maker() as session:
            try:
                query = (
                    select(DocumentChunkDB)
                    .options(selectinload(DocumentChunkDB.document))
                    .where(DocumentChunkDB.id == UUID(chunk_id))
                )

                result = await session.execute(query)
                chunk = result.scalar_one_or_none()

                if not chunk:
                    return None

                return {
                    "id": str(chunk.id),
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "document_id": str(chunk.document_id),
                    "document_filename": (
                        chunk.document.filename if chunk.document else None
                    ),
                    "embedding": chunk.embedding,
                    "metadata": chunk.meta_data or {},
                }

            except Exception as e:
                logger.error(f"Error getting chunk {chunk_id}: {str(e)}")
                raise

    async def get_document_chunks(
        self, document_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document

        Args:
            document_id: ID of the document
            skip: Number of chunks to skip
            limit: Maximum number of chunks to return

        Returns:
            List of chunks for the document
        """
        async with async_session_maker() as session:
            try:
                query = (
                    select(DocumentChunkDB)
                    .where(DocumentChunkDB.document_id == document_id)
                    .order_by(DocumentChunkDB.chunk_index)
                    .offset(skip)
                    .limit(limit)
                )

                result = await session.execute(query)
                chunks = result.scalars().all()

                chunk_list = []
                for chunk in chunks:
                    chunk_data = {
                        "id": str(chunk.id),
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "document_id": str(chunk.document_id),
                        "metadata": chunk.meta_data or {},
                    }
                    chunk_list.append(chunk_data)

                return chunk_list

            except Exception as e:
                logger.error(f"Error getting document chunks: {str(e)}")
                raise

    async def optimize_vector_index(self) -> bool:
        """
        Optimize the vector index for better performance
        This recreates the IVFFlat index with updated statistics

        Returns:
            True if optimization succeeded
        """
        async with async_session_maker() as session:
            try:
                # Drop existing index
                await session.execute(
                    text("DROP INDEX IF EXISTS idx_document_chunks_embedding_cosine")
                )

                # Recreate index with optimized parameters
                # Lists parameter should be roughly sqrt(total_rows)
                count_result = await session.execute(
                    select(func.count(DocumentChunkDB.id))
                )
                total_chunks = count_result.scalar() or 0

                # Calculate optimal lists parameter (sqrt of total rows, min 1, max 1000)
                lists = max(1, min(1000, int(total_chunks**0.5)))

                await session.execute(
                    text(
                        f"""
                    CREATE INDEX idx_document_chunks_embedding_cosine 
                    ON document_chunks 
                    USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = {lists})
                """
                    )
                )

                await session.commit()

                logger.info(
                    f"Optimized vector index with {lists} lists for "
                    f"{total_chunks} chunks"
                )
                return True

            except Exception as e:
                await session.rollback()
                logger.error(f"Error optimizing vector index: {str(e)}")
                raise

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector index

        Returns:
            Dictionary with index statistics
        """
        async with async_session_maker() as session:
            try:
                # Get total number of chunks
                count_result = await session.execute(
                    select(func.count(DocumentChunkDB.id))
                )
                total_chunks = count_result.scalar() or 0

                # Get index size information
                index_size_result = await session.execute(
                    text(
                        """
                    SELECT pg_size_pretty(pg_total_relation_size('idx_document_chunks_embedding_cosine')) as index_size
                """
                    )
                )
                index_size = index_size_result.scalar() or "0 bytes"

                # Get table size information
                table_size_result = await session.execute(
                    text(
                        """
                    SELECT pg_size_pretty(pg_total_relation_size('document_chunks')) as table_size
                """
                    )
                )
                table_size = table_size_result.scalar() or "0 bytes"

                return {
                    "total_chunks": total_chunks,
                    "embedding_dimension": self.embedding_dimension,
                    "index_size": index_size,
                    "table_size": table_size,
                }

            except Exception as e:
                logger.error(f"Error getting index stats: {str(e)}")
                raise


class DocumentChunker:
    """Utility class for chunking documents into optimal segments for embedding"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
    ):
        """
        Initialize document chunker

        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to use for splitting (in order of preference)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",  # Paragraph breaks
            "\n",  # Line breaks
            ". ",  # Sentence endings
            "! ",  # Exclamation sentences
            "? ",  # Question sentences
            "; ",  # Semicolons
            ", ",  # Commas
            " ",  # Spaces
            "",  # Character level (fallback)
        ]

    def chunk_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap

        Args:
            text: Text to chunk
            metadata: Optional metadata to include with each chunk

        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text.strip():
            return []

        chunks = []
        chunk_index = 0

        # Split text using the most appropriate separator
        text_chunks = self._split_text_recursive(text, self.separators)

        # Combine chunks to reach target size with overlap
        current_chunk = ""

        for i, chunk in enumerate(text_chunks):
            # If adding this chunk would exceed the size limit
            if len(current_chunk) + len(chunk) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_data = {
                    "content": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "metadata": {
                        **(metadata or {}),
                        "start_char": len(
                            "".join(text_chunks[: i - len(current_chunk.split())])
                        ),
                    },
                }
                chunks.append(chunk_data)
                chunk_index += 1

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + chunk
            else:
                # Add to current chunk
                current_chunk += (" " if current_chunk else "") + chunk

        # Add final chunk if it has content
        if current_chunk.strip():
            chunk_data = {
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "metadata": metadata or {},
            }
            chunks.append(chunk_data)

        return chunks

    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using the best available separator"""
        if not separators:
            return [text]

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            # Character-level split as fallback
            return list(text)

        splits = text.split(separator)

        # If we got good splits, return them
        if len(splits) > 1:
            final_chunks = []
            for split in splits:
                if len(split) > self.chunk_size:
                    # Recursively split large chunks
                    sub_chunks = self._split_text_recursive(split, remaining_separators)
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(split)
            return final_chunks
        else:
            # Try next separator
            return self._split_text_recursive(text, remaining_separators)

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk"""
        if len(text) <= self.chunk_overlap:
            return text

        # Try to find a good breaking point for overlap
        overlap_text = text[-self.chunk_overlap :]

        # Try to break at word boundary
        space_index = overlap_text.find(" ")
        if space_index > 0:
            overlap_text = overlap_text[space_index + 1 :]

        return overlap_text
