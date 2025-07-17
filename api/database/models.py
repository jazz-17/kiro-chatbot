from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, Integer, 
    ForeignKey, JSON, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

from .base import Base


class UserDB(Base):
    """SQLAlchemy User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    encrypted_api_keys = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    conversations = relationship("ConversationDB", back_populates="user", cascade="all, delete-orphan")
    rag_debug_logs = relationship("RAGDebugLogDB", back_populates="user", cascade="all, delete-orphan")


class ConversationDB(Base):
    """SQLAlchemy Conversation model"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)
    meta_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    user = relationship("UserDB", back_populates="conversations")
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")
    rag_debug_logs = relationship("RAGDebugLogDB", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_created_at", "created_at"),
    )


class MessageDB(Base):
    """SQLAlchemy Message model"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=False, default=list)
    meta_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    conversation = relationship("ConversationDB", back_populates="messages")
    rag_debug_logs = relationship("RAGDebugLogDB", back_populates="message", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_created_at", "created_at"),
    )


class DocumentDB(Base):
    """SQLAlchemy Document model"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    s3_key = Column(String(500), nullable=False, unique=True)
    processed = Column(Boolean, nullable=False, default=False)
    meta_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    chunks = relationship("DocumentChunkDB", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_documents_filename", "filename"),
        Index("idx_documents_processed", "processed"),
        Index("idx_documents_created_at", "created_at"),
    )


class DocumentChunkDB(Base):
    """SQLAlchemy DocumentChunk model with vector support"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    # Vector embedding - will be created as vector type in migration
    embedding = Column(ARRAY(float), nullable=False)
    meta_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    document = relationship("DocumentDB", back_populates="chunks")
    
    # Indexes - vector indexes will be created in migration
    __table_args__ = (
        Index("idx_document_chunks_document_id", "document_id"),
        Index("idx_document_chunks_chunk_index", "chunk_index"),
    )


class RAGDebugLogDB(Base):
    """SQLAlchemy RAGDebugLog model"""
    __tablename__ = "rag_debug_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    retrieved_chunks = Column(JSON, nullable=False)
    search_scores = Column(ARRAY(float), nullable=False)
    prompt_template = Column(Text, nullable=False)
    final_prompt = Column(Text, nullable=False)
    response_meta_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    conversation = relationship("ConversationDB", back_populates="rag_debug_logs")
    message = relationship("MessageDB", back_populates="rag_debug_logs")
    user = relationship("UserDB", back_populates="rag_debug_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_rag_debug_logs_conversation_id", "conversation_id"),
        Index("idx_rag_debug_logs_message_id", "message_id"),
        Index("idx_rag_debug_logs_user_id", "user_id"),
        Index("idx_rag_debug_logs_created_at", "created_at"),
    )