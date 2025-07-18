"""
SQLAlchemy Core implementation of ConversationRepository.
This replaces the ORM-based repository with explicit SQL operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import select, insert, update, delete, and_, func, join
from sqlalchemy.exc import IntegrityError

from repositories.base import BaseRepository
from database.tables import conversations_table, messages_table, users_table
from models.conversation import Conversation, Message


class ConversationRepository(BaseRepository):
    """SQLAlchemy Core implementation of ConversationRepository"""
    
    def __init__(self, connection: AsyncConnection):
        self.connection = connection
    
    async def create(self, entity: Conversation) -> Conversation:
        """Create a new conversation"""
        try:
            # Prepare insert values
            insert_values = {
                "id": entity.id or uuid4(),
                "user_id": entity.user_id,
                "title": entity.title,
                "provider": entity.provider,
                "meta_data": entity.metadata,
                "created_at": entity.created_at or datetime.utcnow(),
                "updated_at": entity.updated_at
            }
            
            # Execute insert and get the result
            stmt = insert(conversations_table).values(**insert_values).returning(conversations_table)
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return Conversation(
                    id=row.id,
                    user_id=row.user_id,
                    title=row.title,
                    provider=row.provider,
                    meta_data=row.meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    messages=[]  # Empty messages list for new conversation
                )
            else:
                raise ValueError("Failed to create conversation")
                
        except IntegrityError as e:
            raise ValueError(f"Conversation creation failed: {str(e)}")
    
    async def get_by_id(self, entity_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID with messages"""
        # Get conversation
        conv_stmt = select(conversations_table).where(conversations_table.c.id == entity_id)
        conv_result = await self.connection.execute(conv_stmt)
        conv_row = conv_result.fetchone()
        
        if not conv_row:
            return None
        
        # Get messages for this conversation
        msg_stmt = (
            select(messages_table)
            .where(messages_table.c.conversation_id == entity_id)
            .order_by(messages_table.c.created_at.asc())
        )
        msg_result = await self.connection.execute(msg_stmt)
        msg_rows = msg_result.fetchall()
        
        # Build messages list
        messages = [
            Message(
                id=msg_row.id,
                conversation_id=msg_row.conversation_id,
                role=msg_row.role,
                content=msg_row.content,
                citations=msg_row.citations,
                meta_data=msg_row.meta_data,
                created_at=msg_row.created_at,
                updated_at=msg_row.updated_at
            )
            for msg_row in msg_rows
        ]
        
        return Conversation(
            id=conv_row.id,
            user_id=conv_row.user_id,
            title=conv_row.title,
            provider=conv_row.provider,
            meta_data=conv_row.meta_data,
            created_at=conv_row.created_at,
            updated_at=conv_row.updated_at,
            messages=messages
        )
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all conversations with pagination"""
        stmt = (
            select(conversations_table)
            .offset(skip)
            .limit(limit)
            .order_by(conversations_table.c.updated_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        conversations = []
        for row in rows:
            # Get messages for each conversation
            msg_stmt = (
                select(messages_table)
                .where(messages_table.c.conversation_id == row.id)
                .order_by(messages_table.c.created_at.asc())
            )
            msg_result = await self.connection.execute(msg_stmt)
            msg_rows = msg_result.fetchall()
            
            messages = [
                Message(
                    id=msg_row.id,
                    conversation_id=msg_row.conversation_id,
                    role=msg_row.role,
                    content=msg_row.content,
                    citations=msg_row.citations,
                    meta_data=msg_row.meta_data,
                    created_at=msg_row.created_at,
                    updated_at=msg_row.updated_at
                )
                for msg_row in msg_rows
            ]
            
            conversations.append(Conversation(
                id=row.id,
                user_id=row.user_id,
                title=row.title,
                provider=row.provider,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at,
                messages=messages
            ))
        
        return conversations
    
    async def update(self, entity_id: UUID, update_data: Dict[str, Any]) -> Optional[Conversation]:
        """Update conversation by ID"""
        try:
            # Handle metadata field mapping
            if 'metadata' in update_data:
                update_data['meta_data'] = update_data.pop('metadata')
            
            # Add updated_at timestamp
            update_data = {**update_data, "updated_at": datetime.utcnow()}
            
            stmt = (
                update(conversations_table)
                .where(conversations_table.c.id == entity_id)
                .values(**update_data)
                .returning(conversations_table)
            )
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return Conversation(
                    id=row.id,
                    user_id=row.user_id,
                    title=row.title,
                    provider=row.provider,
                    meta_data=row.meta_data,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    messages=[]  # Don't load messages for simple update
                )
            return None
            
        except IntegrityError as e:
            raise ValueError(f"Conversation update failed: {str(e)}")
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete conversation by ID"""
        stmt = delete(conversations_table).where(conversations_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.rowcount > 0
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if conversation exists"""
        stmt = select(conversations_table.c.id).where(conversations_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.fetchone() is not None
    
    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by user ID"""
        stmt = (
            select(conversations_table)
            .where(conversations_table.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(conversations_table.c.updated_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        conversations = []
        for row in rows:
            # Get messages for each conversation
            msg_stmt = (
                select(messages_table)
                .where(messages_table.c.conversation_id == row.id)
                .order_by(messages_table.c.created_at.asc())
            )
            msg_result = await self.connection.execute(msg_stmt)
            msg_rows = msg_result.fetchall()
            
            messages = [
                Message(
                    id=msg_row.id,
                    conversation_id=msg_row.conversation_id,
                    role=msg_row.role,
                    content=msg_row.content,
                    citations=msg_row.citations,
                    meta_data=msg_row.meta_data,
                    created_at=msg_row.created_at,
                    updated_at=msg_row.updated_at
                )
                for msg_row in msg_rows
            ]
            
            conversations.append(Conversation(
                id=row.id,
                user_id=row.user_id,
                title=row.title,
                provider=row.provider,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at,
                messages=messages
            ))
        
        return conversations
    
    async def add_message(self, conversation_id: UUID, message: Message) -> Message:
        """Add message to conversation"""
        try:
            # Verify conversation exists
            conv_stmt = select(conversations_table.c.id).where(conversations_table.c.id == conversation_id)
            conv_result = await self.connection.execute(conv_stmt)
            if not conv_result.fetchone():
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Prepare message insert values
            insert_values = {
                "id": message.id or uuid4(),
                "conversation_id": conversation_id,
                "role": message.role,
                "content": message.content,
                "citations": message.citations,
                "meta_data": message.metadata,
                "created_at": message.created_at or datetime.utcnow(),
                "updated_at": message.updated_at
            }
            
            # Insert message
            msg_stmt = insert(messages_table).values(**insert_values).returning(messages_table)
            msg_result = await self.connection.execute(msg_stmt)
            msg_row = msg_result.fetchone()
            
            if not msg_row:
                raise ValueError("Failed to create message")
            
            # Update conversation's updated_at timestamp
            conv_update_stmt = (
                update(conversations_table)
                .where(conversations_table.c.id == conversation_id)
                .values(updated_at=msg_row.created_at)
            )
            await self.connection.execute(conv_update_stmt)
            
            return Message(
                id=msg_row.id,
                conversation_id=msg_row.conversation_id,
                role=msg_row.role,
                content=msg_row.content,
                citations=msg_row.citations,
                meta_data= msg_row.meta_data,
                created_at=msg_row.created_at,
                updated_at=msg_row.updated_at
            )
            
        except IntegrityError as e:
            raise ValueError(f"Message creation failed: {str(e)}")
    
    async def get_messages(self, conversation_id: UUID, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get messages for a conversation"""
        stmt = (
            select(messages_table)
            .where(messages_table.c.conversation_id == conversation_id)
            .offset(skip)
            .limit(limit)
            .order_by(messages_table.c.created_at.asc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            Message(
                id=row.id,
                conversation_id=row.conversation_id,
                role=row.role,
                content=row.content,
                citations=row.citations,
                meta_data=row.meta_data,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def get_conversation_with_user_check(self, conversation_id: UUID, user_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID with user ownership check"""
        stmt = (
            select(conversations_table)
            .where(and_(
                conversations_table.c.id == conversation_id,
                conversations_table.c.user_id == user_id
            ))
        )
        result = await self.connection.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
        
        # Get messages
        msg_stmt = (
            select(messages_table)
            .where(messages_table.c.conversation_id == conversation_id)
            .order_by(messages_table.c.created_at.asc())
        )
        msg_result = await self.connection.execute(msg_stmt)
        msg_rows = msg_result.fetchall()
        
        messages = [
            Message(
                id=msg_row.id,
                conversation_id=msg_row.conversation_id,
                role=msg_row.role,
                content=msg_row.content,
                citations=msg_row.citations,
                meta_data=msg_row.meta_data,
                created_at=msg_row.created_at,
                updated_at=msg_row.updated_at
            )
            for msg_row in msg_rows
        ]
        
        return Conversation(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            provider=row.provider,
            meta_data=row.meta_data,
            created_at=row.created_at,
            updated_at=row.updated_at,
            messages=messages
        )
    
    async def delete_user_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Delete conversation with user ownership check"""
        stmt = delete(conversations_table).where(
            and_(
                conversations_table.c.id == conversation_id,
                conversations_table.c.user_id == user_id
            )
        )
        result = await self.connection.execute(stmt)
        return result.rowcount > 0
    
    async def get_conversation_count_by_user(self, user_id: UUID) -> int:
        """Get total number of conversations for a user"""
        stmt = select(func.count(conversations_table.c.id)).where(conversations_table.c.user_id == user_id)
        result = await self.connection.execute(stmt)
        return result.scalar() or 0