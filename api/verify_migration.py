#!/usr/bin/env python3
"""
Script to verify that the migration file is properly structured and contains all required elements.
"""

import os
import sys

def verify_migration_file():
    """Verify that the migration file contains all required elements"""
    migration_path = "alembic/versions/001_initial_migration_with_pgvector_support.py"
    
    if not os.path.exists(migration_path):
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, 'r') as f:
        content = f.read()
    
    # Check for required elements
    required_elements = [
        "CREATE EXTENSION IF NOT EXISTS vector",
        "op.create_table('users'",
        "op.create_table('conversations'", 
        "op.create_table('messages'",
        "op.create_table('documents'",
        "op.create_table('document_chunks'",
        "op.create_table('rag_debug_logs'",
        "ALTER TABLE document_chunks ADD COLUMN embedding vector(1536)",
        "CREATE INDEX idx_document_chunks_embedding_cosine",
        "encrypted_api_keys",
        "preferences",
        "citations",
        "meta_data",
        "response_meta_data"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print("❌ Migration file is missing required elements:")
        for element in missing_elements:
            print(f"   - {element}")
        return False
    
    print("✓ Migration file contains all required elements")
    
    # Check for proper table structure
    tables = ["users", "conversations", "messages", "documents", "document_chunks", "rag_debug_logs"]
    for table in tables:
        if f"op.create_table('{table}'" not in content:
            print(f"❌ Missing table creation: {table}")
            return False
        if f"op.drop_table('{table}')" not in content:
            print(f"❌ Missing table drop in downgrade: {table}")
            return False
    
    print("✓ All tables have proper create and drop statements")
    
    # Check for pgvector extension
    if "CREATE EXTENSION IF NOT EXISTS vector" not in content:
        print("❌ Missing pgvector extension creation")
        return False
    
    if "DROP EXTENSION IF EXISTS vector" not in content:
        print("❌ Missing pgvector extension drop in downgrade")
        return False
    
    print("✓ pgvector extension is properly handled")
    
    # Check for vector column and index
    if "embedding vector(1536)" not in content:
        print("❌ Missing vector column definition")
        return False
    
    if "vector_cosine_ops" not in content:
        print("❌ Missing vector similarity index")
        return False
    
    print("✓ Vector column and similarity index are properly defined")
    
    return True

def verify_alembic_config():
    """Verify that Alembic configuration is properly set up"""
    alembic_ini_path = "alembic.ini"
    
    if not os.path.exists(alembic_ini_path):
        print(f"❌ Alembic config file not found: {alembic_ini_path}")
        return False
    
    with open(alembic_ini_path, 'r') as f:
        content = f.read()
    
    if "postgresql://postgres:postgres@localhost:5432/chatbot_db" not in content:
        print("❌ Database URL not properly configured in alembic.ini")
        return False
    
    print("✓ Alembic configuration is properly set up")
    return True

def verify_env_py():
    """Verify that Alembic env.py is properly configured"""
    env_py_path = "alembic/env.py"
    
    if not os.path.exists(env_py_path):
        print(f"❌ Alembic env.py file not found: {env_py_path}")
        return False
    
    with open(env_py_path, 'r') as f:
        content = f.read()
    
    required_imports = [
        "from database.base import Base",
        "from database.models import *",
        "target_metadata = Base.metadata"
    ]
    
    for import_stmt in required_imports:
        if import_stmt not in content:
            print(f"❌ Missing import in env.py: {import_stmt}")
            return False
    
    print("✓ Alembic env.py is properly configured")
    return True

if __name__ == "__main__":
    print("=== Migration Verification ===\n")
    
    success = True
    
    success &= verify_migration_file()
    success &= verify_alembic_config()
    success &= verify_env_py()
    
    if success:
        print("\n🎉 All migration components are properly configured!")
        print("\nNext steps:")
        print("1. Start PostgreSQL database")
        print("2. Create database: CREATE DATABASE chatbot_db;")
        print("3. Run migration: uv run alembic upgrade head")
    else:
        print("\n❌ Some migration components need to be fixed.")
        sys.exit(1)