"""
SQLAlchemy Core implementation of Document and Vector repositories.
This replaces the ORM-based repositories with explicit SQL operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import select, insert, update, delete, and_, func, text
from sqlalchemy.exc import IntegrityError
import numpy as np

from repositories.base import BaseRepository
from database.tables import documents_table, document_chunks_table
from models.document import Document, DocumentChunk


class DocumentRepository(BaseRepository[Document]):
    """SQLAlchemy Core implementation of DocumentRepository"""
    
    def __init__(self, connection: AsyncConnection):
        self.connection = connection
    
    async def create(self, entity: Document) -> Document:
        """Create a new document"""
        try:
            # Prepare insert values
            insert_values = {
                "id": entity.id or uuid4(),
                "filename": entity.filename,
                "content_type": entity.content_type,
                "s3_key": entity.s3_key,
                "processed": entity.processed,
                "meta_data": entity.meta_data,
                "created_at": entity.created_at or datetime.utcnow(),
                "updated_at": entity.updated_at
            }
            
            # Execute insert and get the result
            stmt = insert(documents_table).values(**insert_values).returning(documents_table)
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return Document(
                    id=row.id,
                    filename=row.filename,
                    content_type=row.content_type,
                    s3_key=row.s3_key,
                    processed=row.processed,
                    meta_data=row.meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            else:
                raise ValueError("Failed to create document")
                
        except IntegrityError as e:
            raise ValueError(f"Document creation failed: {str(e)}")
    
    async def get_by_id(self, entity_id: UUID) -> Optional[Document]:
        """Get document by ID"""
        stmt = select(documents_table).where(documents_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        row = result.fetchone()
        
        if row:
            return Document(
                id=row.id,
                filename=row.filename,
                content_type=row.content_type,
                s3_key=row.s3_key,
                processed=row.processed,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        return None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get all documents with pagination"""
        stmt = (
            select(documents_table)
            .offset(skip)
            .limit(limit)
            .order_by(documents_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            Document(
                id=row.id,
                filename=row.filename,
                content_type=row.content_type,
                s3_key=row.s3_key,
                processed=row.processed,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def update(self, entity_id: UUID, update_data: Dict[str, Any]) -> Optional[Document]:
        """Update document by ID"""
        try:
            # Handle meta_data field mapping
            if 'meta_data' in update_data:
                update_data['meta_data'] = update_data.pop('meta_data')
            
            # Add updated_at timestamp
            update_data = {**update_data, "updated_at": datetime.utcnow()}
            
            stmt = (
                update(documents_table)
                .where(documents_table.c.id == entity_id)
                .values(**update_data)
                .returning(documents_table)
            )
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return Document(
                    id=row.id,
                    filename=row.filename,
                    content_type=row.content_type,
                    s3_key=row.s3_key,
                    processed=row.processed,
                    meta_data=row.meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            return None
            
        except IntegrityError as e:
            raise ValueError(f"Document update failed: {str(e)}")
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete document by ID"""
        stmt = delete(documents_table).where(documents_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.rowcount > 0
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if document exists"""
        stmt = select(documents_table.c.id).where(documents_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.fetchone() is not None
    
    async def get_by_s3_key(self, s3_key: str) -> Optional[Document]:
        """Get document by S3 key"""
        stmt = select(documents_table).where(documents_table.c.s3_key == s3_key)
        result = await self.connection.execute(stmt)
        row = result.fetchone()
        
        if row:
            return Document(
                id=row.id,
                filename=row.filename,
                content_type=row.content_type,
                s3_key=row.s3_key,
                processed=row.processed,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        return None
    
    async def get_unprocessed_documents(self, limit: int = 50) -> List[Document]:
        """Get unprocessed documents for background processing"""
        stmt = (
            select(documents_table)
            .where(documents_table.c.processed == False)
            .limit(limit)
            .order_by(documents_table.c.created_at.asc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            Document(
                id=row.id,
                filename=row.filename,
                content_type=row.content_type,
                s3_key=row.s3_key,
                processed=row.processed,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def mark_as_processed(self, document_id: UUID) -> Optional[Document]:
        """Mark document as processed"""
        return await self.update(document_id, {"processed": True})
    
    async def get_by_filename_pattern(self, pattern: str, limit: int = 100) -> List[Document]:
        """Get documents by filename pattern"""
        stmt = (
            select(documents_table)
            .where(documents_table.c.filename.ilike(f"%{pattern}%"))
            .limit(limit)
            .order_by(documents_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            Document(
                id=row.id,
                filename=row.filename,
                content_type=row.content_type,
                s3_key=row.s3_key,
                processed=row.processed,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """SQLAlchemy Core implementation of DocumentChunkRepository with vector search"""
    
    def __init__(self, connection: AsyncConnection):
        self.connection = connection
    
    async def create(self, entity: DocumentChunk) -> DocumentChunk:
        """Create a new document chunk"""
        try:
            # Prepare insert values
            insert_values = {
                "id": entity.id or uuid4(),
                "document_id": entity.document_id,
                "content": entity.content,
                "chunk_index": entity.chunk_index,
                "embedding": entity.embedding,
                "meta_data": entity.meta_data,
                "created_at": entity.created_at or datetime.utcnow(),
                "updated_at": entity.updated_at
            }
            
            # Execute insert and get the result
            stmt = insert(document_chunks_table).values(**insert_values).returning(document_chunks_table)
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return DocumentChunk(
                    id=row.id,
                    document_id=row.document_id,
                    content=row.content,
                    chunk_index=row.chunk_index,
                    embedding=row.embedding,
                    meta_data=row.meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            else:
                raise ValueError("Failed to create document chunk")
                
        except IntegrityError as e:
            raise ValueError(f"Document chunk creation failed: {str(e)}")
    
    async def get_by_id(self, entity_id: UUID) -> Optional[DocumentChunk]:
        """Get document chunk by ID"""
        stmt = select(document_chunks_table).where(document_chunks_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        row = result.fetchone()
        
        if row:
            return DocumentChunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                chunk_index=row.chunk_index,
                embedding=row.embedding,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        return None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[DocumentChunk]:
        """Get all document chunks with pagination"""
        stmt = (
            select(document_chunks_table)
            .offset(skip)
            .limit(limit)
            .order_by(document_chunks_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            DocumentChunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                chunk_index=row.chunk_index,
                embedding=row.embedding,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def update(self, entity_id: UUID, update_data: Dict[str, Any]) -> Optional[DocumentChunk]:
        """Update document chunk by ID"""
        try:
            # Handle meta_data field mapping
            if 'meta_data' in update_data:
                update_data['meta_data'] = update_data.pop('meta_data')
            
            # Add updated_at timestamp
            update_data = {**update_data, "updated_at": datetime.utcnow()}
            
            stmt = (
                update(document_chunks_table)
                .where(document_chunks_table.c.id == entity_id)
                .values(**update_data)
                .returning(document_chunks_table)
            )
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return DocumentChunk(
                    id=row.id,
                    document_id=row.document_id,
                    content=row.content,
                    chunk_index=row.chunk_index,
                    embedding=row.embedding,
                    meta_data=row.meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            return None
            
        except IntegrityError as e:
            raise ValueError(f"Document chunk update failed: {str(e)}")
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete document chunk by ID"""
        stmt = delete(document_chunks_table).where(document_chunks_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.rowcount > 0
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if document chunk exists"""
        stmt = select(document_chunks_table.c.id).where(document_chunks_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.fetchone() is not None
    
    async def get_by_document_id(self, document_id: UUID) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        stmt = (
            select(document_chunks_table)
            .where(document_chunks_table.c.document_id == document_id)
            .order_by(document_chunks_table.c.chunk_index.asc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            DocumentChunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                chunk_index=row.chunk_index,
                embedding=row.embedding,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def delete_by_document_id(self, document_id: UUID) -> int:
        """Delete all chunks for a document"""
        stmt = delete(document_chunks_table).where(document_chunks_table.c.document_id == document_id)
        result = await self.connection.execute(stmt)
        return result.rowcount
    
    async def similarity_search(
        self, 
        query_embedding: List[float], 
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Perform similarity search using pgvector"""
        try:
            # Convert embedding to string format for pgvector
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Use pgvector cosine similarity search with JOIN to get document info
            query_sql = text("""
                SELECT 
                    dc.id,
                    dc.document_id,
                    dc.content,
                    dc.chunk_index,
                    dc.meta_data,
                    dc.created_at,
                    d.filename,
                    d.content_type,
                    1 - (dc.embedding <=> :embedding::vector) as similarity_score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE 1 - (dc.embedding <=> :embedding::vector) >= :threshold
                ORDER BY dc.embedding <=> :embedding::vector
                LIMIT :limit
            """)
            
            result = await self.connection.execute(
                query_sql, 
                {
                    "embedding": embedding_str,
                    "threshold": threshold,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            
            search_results = []
            for row in rows:
                search_results.append({
                    "chunk_id": str(row.id),
                    "document_id": str(row.document_id),
                    "content": row.content,
                    "chunk_index": row.chunk_index,
                    "meta_data": row.meta_data,
                    "filename": row.filename,
                    "content_type": row.content_type,
                    "similarity_score": float(row.similarity_score),
                    "created_at": row.created_at
                })
            
            return search_results
            
        except Exception as e:
            # Fallback to array-based similarity if pgvector is not available
            return await self._array_similarity_search(query_embedding, limit, threshold)
    
    async def _array_similarity_search(
        self, 
        query_embedding: List[float], 
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Fallback similarity search using array operations"""
        # Get chunks with document info
        stmt = (
            select(
                document_chunks_table.c.id,
                document_chunks_table.c.document_id,
                document_chunks_table.c.content,
                document_chunks_table.c.chunk_index,
                document_chunks_table.c.embedding,
                document_chunks_table.c.meta_data,
                document_chunks_table.c.created_at,
                documents_table.c.filename,
                documents_table.c.content_type
            )
            .select_from(
                document_chunks_table.join(
                    documents_table, 
                    document_chunks_table.c.document_id == documents_table.c.id
                )
            )
            .limit(limit * 2)  # Get more to filter by threshold
        )
        
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        # Simple cosine similarity calculation (this is inefficient for large datasets)
        search_results = []
        query_vec = np.array(query_embedding)
        
        for row in rows:
            chunk_vec = np.array(row.embedding)
            
            # Cosine similarity
            dot_product = np.dot(query_vec, chunk_vec)
            norms = np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
            similarity = dot_product / norms if norms > 0 else 0
            
            if similarity >= threshold:
                search_results.append({
                    "chunk_id": str(row.id),
                    "document_id": str(row.document_id),
                    "content": row.content,
                    "chunk_index": row.chunk_index,
                    "meta_data": row.meta_data,
                    "filename": row.filename,
                    "content_type": row.content_type,
                    "similarity_score": float(similarity),
                    "created_at": row.created_at
                })
        
        # Sort by similarity score descending
        search_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return search_results[:limit]
    
    async def create_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Create multiple document chunks in batch"""
        try:
            # Prepare batch insert values
            insert_values = []
            for chunk in chunks:
                insert_values.append({
                    "id": chunk.id or uuid4(),
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "embedding": chunk.embedding,
                    "meta_data": chunk.meta_data,
                    "created_at": chunk.created_at or datetime.utcnow(),
                    "updated_at": chunk.updated_at
                })
            
            # Execute batch insert
            stmt = insert(document_chunks_table).returning(document_chunks_table)
            result = await self.connection.execute(stmt, insert_values)
            rows = result.fetchall()
            
            return [
                DocumentChunk(
                    id=row.id,
                    document_id=row.document_id,
                    content=row.content,
                    chunk_index=row.chunk_index,
                    embedding=row.embedding,
                    meta_data=row.meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                for row in rows
            ]
            
        except IntegrityError as e:
            raise ValueError(f"Batch chunk creation failed: {str(e)}")