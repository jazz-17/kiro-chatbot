from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from .base import BaseEntity


class Document(BaseEntity):
    """Document model for knowledge base files"""
    filename: str
    content_type: str
    s3_key: str
    processed: bool = False
    meta_data: Dict[str, Any] = Field(default_factory=dict, alias="meta_data")


class DocumentChunk(BaseEntity):
    """Document chunk model for vector storage"""
    document_id: UUID
    content: str
    chunk_index: int
    embedding: List[float]
    meta_data: Dict[str, Any] = Field(default_factory=dict, alias="meta_data")


class RAGDebugLog(BaseEntity):
    """RAG debug log model for pipeline inspection"""
    conversation_id: UUID
    message_id: UUID
    user_id: UUID
    query: str
    retrieved_chunks: List[Dict[str, Any]]
    search_scores: List[float]
    prompt_template: str
    final_prompt: str
    response_meta_data: Dict[str, Any] = Field(alias="response_meta_data")


class DocumentCreate(BaseModel):
    """Schema for document creation"""
    filename: str
    content_type: str
    s3_key: str
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunkCreate(BaseModel):
    """Schema for document chunk creation"""
    document_id: UUID
    content: str
    chunk_index: int
    embedding: List[float]
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class RAGDebugLogCreate(BaseModel):
    """Schema for RAG debug log creation"""
    conversation_id: UUID
    message_id: UUID
    user_id: UUID
    query: str
    retrieved_chunks: List[Dict[str, Any]]
    search_scores: List[float]
    prompt_template: str
    final_prompt: str
    response_meta_data: Dict[str, Any]


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: UUID
    filename: str
    content_type: str
    s3_key: str
    processed: bool
    meta_data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True