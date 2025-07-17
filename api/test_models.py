#!/usr/bin/env python3
"""
Simple test script to verify that all models can be imported and instantiated correctly.
This validates the Pydantic models and SQLAlchemy models work together.
"""

import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_pydantic_models():
    """Test that all Pydantic models can be imported and instantiated"""
    print("Testing Pydantic models...")
    
    # Test base model
    from models.base import BaseEntity
    base = BaseEntity()
    print(f"✓ BaseEntity created with ID: {base.id}")
    
    # Test user models
    from models.user import User, UserCreate, UserResponse
    user_create = UserCreate(email="test@example.com", password="password123")
    print(f"✓ UserCreate: {user_create.email}")
    
    user = User(
        email="test@example.com", 
        password_hash="hashed_password",
        encrypted_api_keys={"openai": "encrypted_key"},
        preferences={"theme": "dark"}
    )
    print(f"✓ User created: {user.email}")
    
    # Test conversation models
    from models.conversation import Conversation, Message, ConversationCreate, MessageCreate
    conv_create = ConversationCreate(title="Test Chat", provider="openai")
    print(f"✓ ConversationCreate: {conv_create.title}")
    
    conversation = Conversation(
        user_id=uuid4(),
        title="Test Conversation",
        provider="openai",
        metadata={"test": "data"}
    )
    print(f"✓ Conversation created: {conversation.title}")
    
    message = Message(
        conversation_id=conversation.id,
        role="user",
        content="Hello, world!",
        citations=[{"source": "doc1", "page": 1}],
        metadata={"timestamp": "2024-01-01"}
    )
    print(f"✓ Message created: {message.content[:20]}...")
    
    # Test document models
    from models.document import Document, DocumentChunk, RAGDebugLog
    document = Document(
        filename="test.pdf",
        content_type="application/pdf",
        s3_key="documents/test.pdf",
        processed=True,
        metadata={"size": 1024}
    )
    print(f"✓ Document created: {document.filename}")
    
    chunk = DocumentChunk(
        document_id=document.id,
        content="This is a test chunk",
        chunk_index=0,
        embedding=[0.1, 0.2, 0.3],
        metadata={"length": 20}
    )
    print(f"✓ DocumentChunk created: {chunk.content[:20]}...")
    
    debug_log = RAGDebugLog(
        conversation_id=conversation.id,
        message_id=message.id,
        user_id=user.id,
        query="test query",
        retrieved_chunks=[{"chunk_id": str(chunk.id), "score": 0.9}],
        search_scores=[0.9, 0.8, 0.7],
        prompt_template="Template: {context}",
        final_prompt="Final prompt with context",
        response_meta_data={"tokens": 100}  # Use the alias name
    )
    print(f"✓ RAGDebugLog created: {debug_log.query}")


def test_sqlalchemy_models():
    """Test that SQLAlchemy models can be imported"""
    print("\nTesting SQLAlchemy models...")
    
    try:
        from database.models import (
            UserDB, ConversationDB, MessageDB, 
            DocumentDB, DocumentChunkDB, RAGDebugLogDB
        )
        print("✓ All SQLAlchemy models imported successfully")
        
        # Test that the models have the expected attributes
        user_attrs = ['id', 'email', 'password_hash', 'encrypted_api_keys', 'preferences']
        for attr in user_attrs:
            assert hasattr(UserDB, attr), f"UserDB missing attribute: {attr}"
        print("✓ UserDB has all required attributes")
        
        conv_attrs = ['id', 'user_id', 'title', 'provider', 'meta_data']
        for attr in conv_attrs:
            assert hasattr(ConversationDB, attr), f"ConversationDB missing attribute: {attr}"
        print("✓ ConversationDB has all required attributes")
        
        msg_attrs = ['id', 'conversation_id', 'role', 'content', 'citations', 'meta_data']
        for attr in msg_attrs:
            assert hasattr(MessageDB, attr), f"MessageDB missing attribute: {attr}"
        print("✓ MessageDB has all required attributes")
        
        doc_attrs = ['id', 'filename', 'content_type', 's3_key', 'processed', 'meta_data']
        for attr in doc_attrs:
            assert hasattr(DocumentDB, attr), f"DocumentDB missing attribute: {attr}"
        print("✓ DocumentDB has all required attributes")
        
        chunk_attrs = ['id', 'document_id', 'content', 'chunk_index', 'embedding', 'meta_data']
        for attr in chunk_attrs:
            assert hasattr(DocumentChunkDB, attr), f"DocumentChunkDB missing attribute: {attr}"
        print("✓ DocumentChunkDB has all required attributes")
        
        debug_attrs = ['id', 'conversation_id', 'message_id', 'user_id', 'query', 'retrieved_chunks', 'search_scores', 'prompt_template', 'final_prompt', 'response_meta_data']
        for attr in debug_attrs:
            assert hasattr(RAGDebugLogDB, attr), f"RAGDebugLogDB missing attribute: {attr}"
        print("✓ RAGDebugLogDB has all required attributes")
        
    except Exception as e:
        print(f"✗ Error importing SQLAlchemy models: {e}")
        return False
    
    return True


def test_database_base():
    """Test that database base configuration can be imported"""
    print("\nTesting database base configuration...")
    
    try:
        from database.base import Base, get_db, engine
        print("✓ Database base components imported successfully")
        print(f"✓ Base metadata: {Base.metadata}")
        print("✓ Database configuration is valid")
        return True
    except Exception as e:
        print(f"✗ Error importing database base: {e}")
        return False


if __name__ == "__main__":
    print("=== Model Validation Test ===\n")
    
    try:
        test_pydantic_models()
        sqlalchemy_ok = test_sqlalchemy_models()
        database_ok = test_database_base()
        
        if sqlalchemy_ok and database_ok:
            print("\n🎉 All tests passed! Models are correctly configured.")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)