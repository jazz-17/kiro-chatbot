"""
SQLAlchemy Core implementation of RAGDebugRepository.
This replaces the ORM-based repository with explicit SQL operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import select, insert, update, delete, and_, func
from sqlalchemy.exc import IntegrityError

from repositories.base import BaseRepository
from database.tables import rag_debug_logs_table
from models.document import RAGDebugLog


class RAGDebugRepository(BaseRepository[RAGDebugLog]):
    """SQLAlchemy Core implementation of RAGDebugRepository"""
    
    def __init__(self, connection: AsyncConnection):
        self.connection = connection
    
    async def create(self, entity: RAGDebugLog) -> RAGDebugLog:
        """Create a new RAG debug log"""
        try:
            # Prepare insert values
            insert_values = {
                "id": entity.id or uuid4(),
                "conversation_id": entity.conversation_id,
                "message_id": entity.message_id,
                "user_id": entity.user_id,
                "query": entity.query,
                "retrieved_chunks": entity.retrieved_chunks,
                "search_scores": entity.search_scores,
                "prompt_template": entity.prompt_template,
                "final_prompt": entity.final_prompt,
                "response_meta_data": entity.response_meta_data,
                "created_at": entity.created_at or datetime.utcnow(),
                "updated_at": entity.updated_at
            }
            
            # Execute insert and get the result
            stmt = insert(rag_debug_logs_table).values(**insert_values).returning(rag_debug_logs_table)
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return RAGDebugLog(
                    id=row.id,
                    conversation_id=row.conversation_id,
                    message_id=row.message_id,
                    user_id=row.user_id,
                    query=row.query,
                    retrieved_chunks=row.retrieved_chunks,
                    search_scores=row.search_scores,
                    prompt_template=row.prompt_template,
                    final_prompt=row.final_prompt,
                    response_meta_data=row.response_meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            else:
                raise ValueError("Failed to create RAG debug log")
                
        except IntegrityError as e:
            raise ValueError(f"RAG debug log creation failed: {str(e)}")
    
    async def get_by_id(self, entity_id: UUID) -> Optional[RAGDebugLog]:
        """Get RAG debug log by ID"""
        stmt = select(rag_debug_logs_table).where(rag_debug_logs_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        row = result.fetchone()
        
        if row:
            return RAGDebugLog(
                id=row.id,
                conversation_id=row.conversation_id,
                message_id=row.message_id,
                user_id=row.user_id,
                query=row.query,
                retrieved_chunks=row.retrieved_chunks,
                search_scores=row.search_scores,
                prompt_template=row.prompt_template,
                final_prompt=row.final_prompt,
                response_meta_data=row.response_meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        return None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[RAGDebugLog]:
        """Get all RAG debug logs with pagination"""
        stmt = (
            select(rag_debug_logs_table)
            .offset(skip)
            .limit(limit)
            .order_by(rag_debug_logs_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            RAGDebugLog(
                id=row.id,
                conversation_id=row.conversation_id,
                message_id=row.message_id,
                user_id=row.user_id,
                query=row.query,
                retrieved_chunks=row.retrieved_chunks,
                search_scores=row.search_scores,
                prompt_template=row.prompt_template,
                final_prompt=row.final_prompt,
                response_meta_data=row.response_meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def update(self, entity_id: UUID, update_data: Dict[str, Any]) -> Optional[RAGDebugLog]:
        """Update RAG debug log by ID"""
        try:
            # Handle meta_data field mapping
            if 'response_meta_data' in update_data:
                update_data['response_meta_data'] = update_data.pop('response_meta_data')
            
            # Add updated_at timestamp
            update_data = {**update_data, "updated_at": datetime.utcnow()}
            
            stmt = (
                update(rag_debug_logs_table)
                .where(rag_debug_logs_table.c.id == entity_id)
                .values(**update_data)
                .returning(rag_debug_logs_table)
            )
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return RAGDebugLog(
                    id=row.id,
                    conversation_id=row.conversation_id,
                    message_id=row.message_id,
                    user_id=row.user_id,
                    query=row.query,
                    retrieved_chunks=row.retrieved_chunks,
                    search_scores=row.search_scores,
                    prompt_template=row.prompt_template,
                    final_prompt=row.final_prompt,
                    response_meta_data=row.response_meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            return None
            
        except IntegrityError as e:
            raise ValueError(f"RAG debug log update failed: {str(e)}")
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete RAG debug log by ID"""
        stmt = delete(rag_debug_logs_table).where(rag_debug_logs_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.rowcount > 0
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if RAG debug log exists"""
        stmt = select(rag_debug_logs_table.c.id).where(rag_debug_logs_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.fetchone() is not None
    
    async def get_by_conversation_id(self, conversation_id: UUID, skip: int = 0, limit: int = 100) -> List[RAGDebugLog]:
        """Get RAG debug logs by conversation ID"""
        stmt = (
            select(rag_debug_logs_table)
            .where(rag_debug_logs_table.c.conversation_id == conversation_id)
            .offset(skip)
            .limit(limit)
            .order_by(rag_debug_logs_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            RAGDebugLog(
                id=row.id,
                conversation_id=row.conversation_id,
                message_id=row.message_id,
                user_id=row.user_id,
                query=row.query,
                retrieved_chunks=row.retrieved_chunks,
                search_scores=row.search_scores,
                prompt_template=row.prompt_template,
                final_prompt=row.final_prompt,
                response_meta_data=row.response_meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def get_by_message_id(self, message_id: UUID) -> Optional[RAGDebugLog]:
        """Get RAG debug log by message ID"""
        stmt = select(rag_debug_logs_table).where(rag_debug_logs_table.c.message_id == message_id)
        result = await self.connection.execute(stmt)
        row = result.fetchone()
        
        if row:
            return RAGDebugLog(
                id=row.id,
                conversation_id=row.conversation_id,
                message_id=row.message_id,
                user_id=row.user_id,
                query=row.query,
                retrieved_chunks=row.retrieved_chunks,
                search_scores=row.search_scores,
                prompt_template=row.prompt_template,
                final_prompt=row.final_prompt,
                response_meta_data=row.response_meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        return None
    
    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[RAGDebugLog]:
        """Get RAG debug logs by user ID"""
        stmt = (
            select(rag_debug_logs_table)
            .where(rag_debug_logs_table.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(rag_debug_logs_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            RAGDebugLog(
                id=row.id,
                conversation_id=row.conversation_id,
                message_id=row.message_id,
                user_id=row.user_id,
                query=row.query,
                retrieved_chunks=row.retrieved_chunks,
                search_scores=row.search_scores,
                prompt_template=row.prompt_template,
                final_prompt=row.final_prompt,
                response_meta_data=row.response_meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def get_conversation_logs_with_user_check(
        self, 
        conversation_id: UUID, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[RAGDebugLog]:
        """Get RAG debug logs for a conversation with user ownership check"""
        stmt = (
            select(rag_debug_logs_table)
            .where(and_(
                rag_debug_logs_table.c.conversation_id == conversation_id,
                rag_debug_logs_table.c.user_id == user_id
            ))
            .offset(skip)
            .limit(limit)
            .order_by(rag_debug_logs_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            RAGDebugLog(
                id=row.id,
                conversation_id=row.conversation_id,
                message_id=row.message_id,
                user_id=row.user_id,
                query=row.query,
                retrieved_chunks=row.retrieved_chunks,
                search_scores=row.search_scores,
                prompt_template=row.prompt_template,
                final_prompt=row.final_prompt,
                response_meta_data=row.response_meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def delete_by_conversation_id(self, conversation_id: UUID) -> int:
        """Delete all RAG debug logs for a conversation"""
        stmt = delete(rag_debug_logs_table).where(rag_debug_logs_table.c.conversation_id == conversation_id)
        result = await self.connection.execute(stmt)
        return result.rowcount
    
    async def delete_by_user_id(self, user_id: UUID) -> int:
        """Delete all RAG debug logs for a user"""
        stmt = delete(rag_debug_logs_table).where(rag_debug_logs_table.c.user_id == user_id)
        result = await self.connection.execute(stmt)
        return result.rowcount
    
    async def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get search analytics for the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get total queries
        total_queries_stmt = (
            select(func.count(rag_debug_logs_table.c.id))
            .where(rag_debug_logs_table.c.created_at >= cutoff_date)
        )
        total_queries_result = await self.connection.execute(total_queries_stmt)
        total_queries = total_queries_result.scalar()
        
        # Get average search scores
        avg_scores_stmt = (
            select(func.avg(func.array_length(rag_debug_logs_table.c.search_scores, 1)))
            .where(rag_debug_logs_table.c.created_at >= cutoff_date)
        )
        avg_scores_result = await self.connection.execute(avg_scores_stmt)
        avg_retrieved_chunks = avg_scores_result.scalar() or 0
        
        # Get unique users
        unique_users_stmt = (
            select(func.count(func.distinct(rag_debug_logs_table.c.user_id)))
            .where(rag_debug_logs_table.c.created_at >= cutoff_date)
        )
        unique_users_result = await self.connection.execute(unique_users_stmt)
        unique_users = unique_users_result.scalar()
        
        return {
            "total_queries": total_queries,
            "avg_retrieved_chunks": float(avg_retrieved_chunks),
            "unique_users": unique_users,
            "period_days": days
        }