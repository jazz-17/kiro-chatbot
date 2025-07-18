"""
Integration tests for file processing with vector database

This module tests the integration between file processing and the vector database
for storing and retrieving processed file content.
"""
import asyncio
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
try:
    from PIL import Image
except ImportError:
    # For environments without PIL, create a mock
    class MockImage:
        @staticmethod
        def new(mode, size, color=None):
            return MockImage()
        
        def save(self, fp, format=None):
            if hasattr(fp, 'write'):
                fp.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # Mock PNG header
    
    Image = MockImage

from services.file_service import FileService, LogFileParser, S3StorageService, ImageAnalyzer
from services.ai_providers import OpenAIProvider
from services.vector_service import PostgreSQLVectorDB, DocumentChunker
from models.document import Document, DocumentChunk
from api.repositories.document_repository import DocumentRepository


class TestFileProcessingVectorIntegration:
    """Test integration between file processing and vector database"""
    
    @pytest.mark.asyncio
    async def test_log_file_to_vector_pipeline(self):
        """Test complete pipeline from log file processing to vector storage"""
        
        # Sample log content with errors and context
        log_content = """
2024-01-15 10:30:45 INFO Application started successfully
2024-01-15 10:30:46 INFO Database connection established
2024-01-15 10:31:15 WARNING High memory usage detected: 85%
2024-01-15 10:31:30 ERROR Database query failed: SELECT * FROM users WHERE id = 12345
2024-01-15 10:31:31 ERROR Connection pool exhausted, rejecting new connections
2024-01-15 10:31:45 FATAL System out of memory, shutting down
Traceback (most recent call last):
  File "app.py", line 123, in process_request
    result = database.execute_query(query)
  File "database.py", line 67, in execute_query
    cursor.execute(sql, params)
  File "psycopg2/cursor.py", line 299, in execute
    raise MemoryError("out of memory")
MemoryError: out of memory
2024-01-15 10:32:00 INFO System restart initiated
"""
        
        # Step 1: Parse log file
        parser = LogFileParser()
        parsed_result = parser.parse_log_content(log_content)
        
        # Verify parsing results
        assert len(parsed_result["errors"]) >= 3  # ERROR and FATAL entries
        assert len(parsed_result["stack_traces"]) >= 1
        assert parsed_result["metadata"]["error_count"] >= 3
        
        # Step 2: Create document chunks from parsed content
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        
        # Create comprehensive context from parsed log
        context_text = f"""
Log File Analysis Summary:
{parsed_result['summary']}

Critical Errors Found:
{'. '.join([error['message'] for error in parsed_result['errors'][:3]])}

Key Events Timeline:
- Application started successfully at 10:30:45
- Memory warning at 10:31:15 (85% usage)
- Database query failures starting at 10:31:30
- System out of memory fatal error at 10:31:45
- System restart at 10:32:00

Technical Details:
- Memory exhaustion led to system failure
- Database connection pool issues
- Query: SELECT * FROM users WHERE id = 12345
"""
        
        chunks = chunker.chunk_text(
            context_text, 
            metadata={
                "source_type": "log_file",
                "error_count": parsed_result["metadata"]["error_count"],
                "log_level": "ERROR",
                "timestamp_range": "2024-01-15 10:30:45 to 10:32:00"
            }
        )
        
        assert len(chunks) >= 1
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        
        # Step 3: Mock vector database operations
        mock_vector_db = AsyncMock(spec=PostgreSQLVectorDB)
        mock_ai_provider = AsyncMock(spec=OpenAIProvider)
        
        # Mock embedding creation
        mock_embeddings = [[0.1] * 1536 for _ in chunks]  # OpenAI embedding dimension
        mock_ai_provider.create_embeddings.return_value = mock_embeddings
        
        # Mock vector storage
        chunk_ids = [str(uuid4()) for _ in chunks]
        mock_vector_db.store_embeddings.return_value = chunk_ids
        
        # Step 4: Store chunks with embeddings
        texts = [chunk["content"] for chunk in chunks]
        embeddings = await mock_ai_provider.create_embeddings(texts)
        
        # Prepare documents for vector storage
        vector_documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_documents.append({
                "content": chunk["content"],
                "embedding": embedding,
                "document_id": uuid4(),
                "chunk_index": i,
                "metadata": chunk["metadata"]
            })
        
        stored_ids = await mock_vector_db.store_embeddings(vector_documents)
        
        # Verify the complete pipeline
        assert len(stored_ids) == len(chunks)
        mock_ai_provider.create_embeddings.assert_called_once_with(texts)
        mock_vector_db.store_embeddings.assert_called_once()
        
        # Verify the stored content includes error information
        stored_content = vector_documents[0]["content"]
        assert "memory" in stored_content.lower()
        assert "database" in stored_content.lower()
        assert "error" in stored_content.lower()
    
    @pytest.mark.asyncio
    async def test_image_analysis_to_vector_pipeline(self):
        """Test pipeline from image analysis to vector storage"""
        
        # Step 1: Mock image analysis
        mock_ai_provider = AsyncMock(spec=OpenAIProvider)
        
        # Mock image analysis result
        analysis_result = """
This screenshot shows a critical system error dialog. The main error message reads:
"Fatal Error: Unable to connect to database server db-prod-01.company.com:5432"

Additional details visible:
- Error Code: DB_CONNECTION_TIMEOUT_001
- Application: Customer Management System v2.1
- Timestamp: 2024-01-15 14:30:25
- Suggested Action: "Contact system administrator"
- Stack trace preview shows connection timeout after 30 seconds

The dialog has a red "X" icon indicating a critical error, and there are options to
"Retry Connection" and "Exit Application". The background shows the application
was in the middle of loading customer data when the error occurred.
"""
        
        mock_ai_provider.analyze_image.return_value = analysis_result
        
        # Create test image
        img = Image.new('RGB', (400, 300), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        test_image = img_bytes.getvalue()
        
        # Step 2: Analyze image
        from services.file_service import ImageAnalyzer
        analyzer = ImageAnalyzer(mock_ai_provider)
        
        image_result = await analyzer.analyze_screenshot(
            test_image, 
            "Analyze this error screenshot for technical support"
        )
        
        # Verify analysis
        assert "analysis" in image_result
        assert "extracted_text" in image_result
        assert "metadata" in image_result
        
        # Step 3: Extract key information for vector storage
        analysis_text = image_result["analysis"]
        extracted_patterns = image_result["extracted_text"]
        
        # Create structured content for vector storage
        structured_content = f"""
Screenshot Analysis - Database Connection Error

Error Summary:
Fatal database connection error preventing application access

Technical Details:
- Error Code: DB_CONNECTION_TIMEOUT_001
- Database Server: db-prod-01.company.com:5432
- Application: Customer Management System v2.1
- Timestamp: 2024-01-15 14:30:25
- Timeout Duration: 30 seconds

User Impact:
- Unable to load customer data
- Application became unresponsive
- User presented with critical error dialog

Recommended Actions:
- Check database server connectivity
- Verify network connectivity to port 5432
- Contact system administrator
- Check database server logs for issues

Visual Context:
{analysis_text}
"""
        
        # Step 4: Create chunks and embeddings
        chunker = DocumentChunker(chunk_size=600, chunk_overlap=50)
        chunks = chunker.chunk_text(
            structured_content,
            metadata={
                "source_type": "screenshot",
                "error_code": "DB_CONNECTION_TIMEOUT_001",
                "application": "Customer Management System",
                "severity": "critical",
                "timestamp": "2024-01-15 14:30:25"
            }
        )
        
        # Step 5: Mock vector storage
        mock_vector_db = AsyncMock(spec=PostgreSQLVectorDB)
        
        texts = [chunk["content"] for chunk in chunks]
        mock_embeddings = [[0.2] * 1536 for _ in chunks]
        mock_ai_provider.create_embeddings.return_value = mock_embeddings
        
        embeddings = await mock_ai_provider.create_embeddings(texts)
        
        # Prepare for vector storage
        vector_documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_documents.append({
                "content": chunk["content"],
                "embedding": embedding,
                "document_id": uuid4(),
                "chunk_index": i,
                "metadata": {
                    **chunk["metadata"],
                    "image_analysis_metadata": image_result["metadata"]
                }
            })
        
        chunk_ids = [str(uuid4()) for _ in chunks]
        mock_vector_db.store_embeddings.return_value = chunk_ids
        
        stored_ids = await mock_vector_db.store_embeddings(vector_documents)
        
        # Verify the pipeline
        assert len(stored_ids) == len(chunks)
        
        # Verify content includes key error information
        stored_content = vector_documents[0]["content"]
        assert "DB_CONNECTION_TIMEOUT_001" in stored_content
        assert "database" in stored_content.lower()
        assert "customer management system" in stored_content.lower()
    
    @pytest.mark.asyncio
    async def test_similarity_search_for_processed_files(self):
        """Test similarity search against processed file content"""
        
        # Mock vector database with stored file content
        mock_vector_db = AsyncMock(spec=PostgreSQLVectorDB)
        mock_ai_provider = AsyncMock(spec=OpenAIProvider)
        
        # Simulate stored content from processed files
        stored_content = [
            {
                "content": "Database connection timeout error. Unable to connect to server db-prod-01:5432 after 30 seconds",
                "metadata": {
                    "source_type": "log_file",
                    "error_code": "DB_TIMEOUT",
                    "severity": "critical"
                },
                "similarity_score": 0.95
            },
            {
                "content": "Memory usage critical at 95%. Application experiencing performance degradation and slow response times",
                "metadata": {
                    "source_type": "screenshot",
                    "error_type": "memory_issue",
                    "severity": "warning"
                },
                "similarity_score": 0.85
            },
            {
                "content": "File not found error when loading configuration. Path: /etc/myapp/config.xml does not exist",
                "metadata": {
                    "source_type": "log_file",
                    "error_type": "file_not_found",
                    "severity": "error"
                },
                "similarity_score": 0.75
            }
        ]
        
        # User query about database issues
        user_query = "My application can't connect to the database and keeps timing out"
        
        # Mock query embedding
        query_embedding = [0.1] * 1536
        mock_ai_provider.create_embeddings.return_value = [query_embedding]
        
        # Mock similarity search results
        mock_vector_db.similarity_search.return_value = stored_content
        
        # Perform similarity search
        query_embeddings = await mock_ai_provider.create_embeddings([user_query])
        search_results = await mock_vector_db.similarity_search(
            query_embedding=query_embeddings[0],
            limit=5,
            threshold=0.7
        )
        
        # Verify search results
        assert len(search_results) == 3  # All results above threshold
        
        # Verify most relevant result is database timeout
        top_result = search_results[0]
        assert top_result["similarity_score"] == 0.95
        assert "database connection timeout" in top_result["content"].lower()
        assert top_result["metadata"]["error_code"] == "DB_TIMEOUT"
        
        # Verify results are ranked by relevance
        scores = [result["similarity_score"] for result in search_results]
        assert scores == sorted(scores, reverse=True)
        
        # Verify API calls
        mock_ai_provider.create_embeddings.assert_called_with([user_query])
        mock_vector_db.similarity_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_file_processing_error_handling(self):
        """Test error handling in the file processing pipeline"""
        
        # Test log parsing with malformed content
        parser = LogFileParser()
        
        # This should not crash but handle gracefully
        try:
            malformed_content = "\x00\x01\x02 invalid binary content \xff\xfe"
            result = parser.parse_log_content(malformed_content)
            
            # Should still return valid structure even with malformed content
            assert "errors" in result
            assert "metadata" in result
            assert result["metadata"]["line_count"] >= 0
            
        except Exception as e:
            # If parsing fails, it should raise LogParsingError
            from services.file_service import LogParsingError
            assert isinstance(e, LogParsingError)
        
        # Test image analysis with invalid image
        mock_ai_provider = AsyncMock(spec=OpenAIProvider)
        analyzer = ImageAnalyzer(mock_ai_provider)
        
        with pytest.raises(Exception):  # Should raise ImageAnalysisError
            await analyzer.analyze_screenshot(b"not an image", "analyze this")
        
        # Test vector storage error handling
        mock_vector_db = AsyncMock(spec=PostgreSQLVectorDB)
        mock_vector_db.store_embeddings.side_effect = Exception("Database connection failed")
        
        # This should handle the error gracefully in a real implementation
        with pytest.raises(Exception):
            await mock_vector_db.store_embeddings([{
                "content": "test content",
                "embedding": [0.1] * 1536,
                "document_id": uuid4(),
                "chunk_index": 0,
                "metadata": {}
            }])


class TestFileServiceConfiguration:
    """Test file service configuration and initialization"""
    
    def test_supported_file_types(self):
        """Test that file service properly defines supported file types"""
        
        # Mock dependencies for FileService initialization
        mock_ai_provider = AsyncMock()
        mock_s3_service = AsyncMock()
        mock_doc_repo = AsyncMock()
        
        file_service = FileService(
            ai_provider=mock_ai_provider,
            s3_service=mock_s3_service,
            document_repository=mock_doc_repo
        )
        
        # Verify supported file types are properly defined
        assert 'image/png' in file_service.SUPPORTED_IMAGE_TYPES
        assert 'image/jpeg' in file_service.SUPPORTED_IMAGE_TYPES
        assert 'text/plain' in file_service.SUPPORTED_TEXT_TYPES
        assert 'application/json' in file_service.SUPPORTED_TEXT_TYPES
        assert 'application/pdf' in file_service.SUPPORTED_DOCUMENT_TYPES
        
        # Verify max file size is reasonable
        assert file_service.MAX_FILE_SIZE > 0
        assert file_service.MAX_FILE_SIZE <= 100 * 1024 * 1024  # Reasonable upper limit
    
    def test_log_file_detection_patterns(self):
        """Test log file detection logic with various file patterns"""
        
        mock_ai_provider = AsyncMock()
        mock_s3_service = AsyncMock()
        mock_doc_repo = AsyncMock()
        
        file_service = FileService(
            ai_provider=mock_ai_provider,
            s3_service=mock_s3_service,
            document_repository=mock_doc_repo
        )
        
        # Test various log file patterns
        test_cases = [
            # (filename, content, expected_result)
            ("application.log", "2024-01-15 ERROR Something failed", True),
            ("debug.txt", "DEBUG Starting process", True),
            ("error_trace.out", "Exception in thread main", True),
            ("audit.log", "INFO User logged in", True),
            ("image.png", "binary image data", False),
            ("document.pdf", "PDF document content", False),
            ("data.json", '{"message": "ERROR: failed"}', True),  # JSON with error
            ("config.xml", "<config>settings</config>", False),
        ]
        
        for filename, content, expected in test_cases:
            result = file_service._is_log_file(filename, content)
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"


if __name__ == "__main__":
    pytest.main([__file__])
