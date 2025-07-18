"""
SQLAlchemy Core table definitions for the AI chatbot application.
This replaces the ORM models with explicit table definitions.
"""

from datetime import datetime
from sqlalchemy import (
    Table,
    Column,
    String,
    DateTime,
    Boolean,
    Text,
    Integer,
    ForeignKey,
    JSON,
    Index,
    func,
    MetaData,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

# Create metadata instance
metadata = MetaData()

# Users table
users_table = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("email", String(255), unique=True, nullable=False, index=True),
    Column("password_hash", String(255), nullable=False),
    Column("encrypted_api_keys", JSON, nullable=True),
    Column("preferences", JSON, nullable=False, default=dict),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("updated_at", DateTime, nullable=True, onupdate=func.now()),
)

# Conversations table
conversations_table = Table(
    "conversations",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("title", String(255), nullable=False),
    Column("provider", String(100), nullable=False),
    Column("meta_data", JSON, nullable=False, default=dict),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("updated_at", DateTime, nullable=True, onupdate=func.now()),
    # Indexes
    Index("idx_conversations_user_id", "user_id"),
    Index("idx_conversations_created_at", "created_at"),
)

# Messages table
messages_table = Table(
    "messages",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column(
        "conversation_id",
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        
    ),
    Column("role", String(20), nullable=False),  # user, assistant, system
    Column("content", Text, nullable=False),
    Column("citations", JSON, nullable=False, default=list),
    Column("meta_data", JSON, nullable=False, default=dict),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("updated_at", DateTime, nullable=True, onupdate=func.now()),
    # Indexes
    Index("idx_messages_conversation_id", "conversation_id"),
    Index("idx_messages_created_at", "created_at"),
)

# Documents table
documents_table = Table(
    "documents",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("filename", String(255), nullable=False),
    Column("content_type", String(100), nullable=False),
    Column("s3_key", String(500), nullable=False, unique=True),
    Column("processed", Boolean, nullable=False, default=False),
    Column("meta_data", JSON, nullable=False, default=dict),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("updated_at", DateTime, nullable=True, onupdate=func.now()),
    # Indexes
    Index("idx_documents_filename", "filename"),
    Index("idx_documents_processed", "processed"),
    Index("idx_documents_created_at", "created_at"),
)

# Document chunks table
document_chunks_table = Table(
    "document_chunks",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column(
        "document_id", UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    ),
    Column("content", Text, nullable=False),
    Column("chunk_index", Integer, nullable=False),
    # Vector embedding - will be created as vector type in migration
    Column("embedding", ARRAY(Float), nullable=False),
    Column("meta_data", JSON, nullable=False, default=dict),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("updated_at", DateTime, nullable=True, onupdate=func.now()),
    # Indexes - vector indexes will be created in migration
    Index("idx_document_chunks_document_id", "document_id"),
    Index("idx_document_chunks_chunk_index", "chunk_index"),
)

# RAG debug logs table
rag_debug_logs_table = Table(
    "rag_debug_logs",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column(
        "conversation_id",
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
    ),
    Column("message_id", UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("query", Text, nullable=False),
    Column("retrieved_chunks", JSON, nullable=False),
    Column("search_scores", ARRAY(Float), nullable=False),
    Column("prompt_template", Text, nullable=False),
    Column("final_prompt", Text, nullable=False),
    Column("response_meta_data", JSON, nullable=False),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("updated_at", DateTime, nullable=True, onupdate=func.now()),
    # Indexes
    Index("idx_rag_debug_logs_conversation_id", "conversation_id"),
    Index("idx_rag_debug_logs_message_id", "message_id"),
    Index("idx_rag_debug_logs_user_id", "user_id"),
    Index("idx_rag_debug_logs_created_at", "created_at"),
)

# Export all tables for easy access
__all__ = [
    "metadata",
    "users_table",
    "conversations_table",
    "messages_table",
    "documents_table",
    "document_chunks_table",
    "rag_debug_logs_table",
]
