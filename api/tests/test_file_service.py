"""
Unit tests for FileService and related components

This module contains comprehensive tests for file processing, log parsing,
image analysis, and S3 storage functionality.
"""
import asyncio
import json
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import UploadFile
from PIL import Image

from services.file_service import (
    FileService,
    LogFileParser,
    ImageAnalyzer,
    S3StorageService,
    FileProcessingError,
    UnsupportedFileTypeError,
    S3StorageError,
    LogParsingError,
    ImageAnalysisError,
)
from services.ai_providers import OpenAIProvider
from models.document import Document, DocumentCreate
from api.repositories.document_repository import DocumentRepository


class TestLogFileParser:
    """Test cases for LogFileParser"""
    
    def setup_method(self):
        self.parser = LogFileParser()
    
    def test_parse_simple_error_log(self):
        """Test parsing a simple error log"""
        log_content = """
2024-01-15 10:30:45 INFO Starting application
2024-01-15 10:30:46 ERROR Database connection failed
2024-01-15 10:30:47 FATAL Unable to start server
"""
        result = self.parser.parse_log_content(log_content)
        
        assert "errors" in result
        assert "stack_traces" in result
        assert "timestamps" in result
        assert "log_levels" in result
        assert "summary" in result
        assert "meta_data" in result
        
        # Check errors
        assert len(result["errors"]) >= 1
        error_messages = [error["message"] for error in result["errors"]]
        assert any("Database connection failed" in msg for msg in error_messages)
        
        # Check meta_data
        assert result["meta_data"]["error_count"] >= 1
        assert result["meta_data"]["line_count"] > 0
    
    def test_parse_stack_trace_log(self):
        """Test parsing log with stack traces"""
        log_content = """
2024-01-15 10:30:45 ERROR An error occurred
Traceback (most recent call last):
  File "app.py", line 25, in main
    process_data()
  File "app.py", line 45, in process_data
    raise ValueError("Invalid input")
ValueError: Invalid input
"""
        result = self.parser.parse_log_content(log_content)
        
        assert len(result["stack_traces"]) >= 1
        stack_trace = result["stack_traces"][0]["trace"]
        assert "Traceback" in stack_trace
        assert "ValueError" in stack_trace
    
    def test_parse_json_log(self):
        """Test parsing JSON structured logs"""
        log_content = """
{"timestamp": "2024-01-15T10:30:45Z", "level": "ERROR", "message": "Service unavailable"}
{"timestamp": "2024-01-15T10:30:46Z", "level": "WARNING", "message": "High memory usage"}
"""
        result = self.parser.parse_log_content(log_content)
        
        assert len(result["errors"]) >= 1
        assert result["meta_data"]["error_count"] >= 1
        assert result["meta_data"]["warning_count"] >= 1
    
    def test_extract_timestamps(self):
        """Test timestamp extraction"""
        log_content = """
2024-01-15 10:30:45 INFO Message 1
2024-01-15T10:30:46.123Z DEBUG Message 2
Jan 15 10:30:47 WARN Message 3
"""
        result = self.parser.parse_log_content(log_content)
        
        assert len(result["timestamps"]) >= 3
        timestamps = [ts["timestamp"] for ts in result["timestamps"]]
        assert any("2024-01-15 10:30:45" in ts for ts in timestamps)
        assert any("2024-01-15T10:30:46.123Z" in ts for ts in timestamps)
    
    def test_parse_empty_log(self):
        """Test parsing empty log content"""
        result = self.parser.parse_log_content("")
        
        assert result["meta_data"]["line_count"] == 1
        assert result["meta_data"]["error_count"] == 0
        assert len(result["errors"]) == 0
    
    def test_parse_invalid_log_raises_error(self):
        """Test that parsing fails gracefully with invalid content"""
        # This should not raise an exception, but handle gracefully
        result = self.parser.parse_log_content("")
        # The method should handle this case
        


class TestImageAnalyzer:
    """Test cases for ImageAnalyzer"""
    
    def setup_method(self):
        self.mock_ai_provider = AsyncMock(spec=OpenAIProvider)
        self.analyzer = ImageAnalyzer(self.mock_ai_provider)
    
    def create_test_image(self) -> bytes:
        """Create a test image as bytes"""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    @pytest.mark.asyncio
    async def test_analyze_screenshot_success(self):
        """Test successful image analysis"""
        test_image = self.create_test_image()
        mock_analysis = "This image shows a red square with error dialog visible"
        
        self.mock_ai_provider.analyze_image.return_value = mock_analysis
        
        result = await self.analyzer.analyze_screenshot(test_image)
        
        assert "analysis" in result
        assert "extracted_text" in result
        assert "meta_data" in result
        assert result["analysis"] == mock_analysis
        assert result["meta_data"]["ai_model"] == "gpt-4o-mini"
        
        # Verify AI provider was called
        self.mock_ai_provider.analyze_image.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_invalid_image(self):
        """Test analysis with invalid image data"""
        invalid_image = b"not an image"
        
        with pytest.raises(ImageAnalysisError):
            await self.analyzer.analyze_screenshot(invalid_image)
    
    @pytest.mark.asyncio
    async def test_analyze_image_ai_provider_error(self):
        """Test handling AI provider errors during analysis"""
        test_image = self.create_test_image()
        self.mock_ai_provider.analyze_image.side_effect = Exception("AI service error")
        
        with pytest.raises(ImageAnalysisError):
            await self.analyzer.analyze_screenshot(test_image)
    
    def test_extract_text_patterns(self):
        """Test extraction of patterns from analysis text"""
        analysis_text = """
        The image shows an error code ERR_001 and exception ValueError.
        File path is C:\\Users\\test\\app.py and URL is https://api.example.com
        """
        
        patterns = self.analyzer._extract_text_patterns(analysis_text)
        
        assert "error_codes" in patterns
        assert "file_paths" in patterns
        assert "urls" in patterns
        assert "exceptions" in patterns
        
        assert "ERR_001" in patterns["error_codes"]
        assert "ValueError" in patterns["exceptions"]
        assert "https://api.example.com" in patterns["urls"]


class TestS3StorageService:
    """Test cases for S3StorageService"""
    
    def setup_method(self):
        self.service = S3StorageService(
            bucket_name="test-bucket",
            endpoint_url="http://localhost:9000"
        )
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self):
        """Test successful file upload"""
        test_content = b"test file content"
        test_key = "test/file.txt"
        
        result_key = await self.service.upload_file(
            file_data=test_content,
            key=test_key,
            content_type="text/plain"
        )
        
        assert result_key == test_key
        
        # Verify file exists in storage
        storage_path = self.service.storage_path / test_key
        assert storage_path.exists()
    
    @pytest.mark.asyncio
    async def test_download_file_success(self):
        """Test successful file download"""
        test_content = b"test file content"
        test_key = "test/download.txt"
        
        # First upload the file
        await self.service.upload_file(
            file_data=test_content,
            key=test_key,
            content_type="text/plain"
        )
        
        # Then download it
        downloaded_content = await self.service.download_file(test_key)
        
        assert downloaded_content == test_content
    
    @pytest.mark.asyncio
    async def test_download_nonexistent_file(self):
        """Test downloading a file that doesn't exist"""
        with pytest.raises(S3StorageError):
            await self.service.download_file("nonexistent/file.txt")
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self):
        """Test successful file deletion"""
        test_content = b"test file content"
        test_key = "test/delete.txt"
        
        # Upload file first
        await self.service.upload_file(
            file_data=test_content,
            key=test_key,
            content_type="text/plain"
        )
        
        # Delete file
        result = await self.service.delete_file(test_key)
        
        assert result is True
        
        # Verify file is deleted
        storage_path = self.service.storage_path / test_key
        assert not storage_path.exists()
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self):
        """Test deleting a file that doesn't exist"""
        result = await self.service.delete_file("nonexistent/file.txt")
        assert result is False
    
    def test_generate_key(self):
        """Test S3 key generation"""
        user_id = uuid4()
        filename = "test_file.txt"
        
        key = self.service.generate_key(filename, user_id)
        
        assert filename in key
        assert str(user_id) in key
        assert "uploads" in key
        
        # Test anonymous key
        anon_key = self.service.generate_key(filename)
        assert "anonymous" in anon_key
        assert filename in anon_key


class TestFileService:
    """Test cases for FileService"""
    
    def setup_method(self):
        self.mock_ai_provider = AsyncMock(spec=OpenAIProvider)
        self.mock_s3_service = AsyncMock(spec=S3StorageService)
        self.mock_document_repository = AsyncMock(spec=DocumentRepository)
        
        self.file_service = FileService(
            ai_provider=self.mock_ai_provider,
            s3_service=self.mock_s3_service,
            document_repository=self.mock_document_repository
        )
    
    def create_mock_upload_file(self, filename: str, content: bytes, content_type: str) -> UploadFile:
        """Create a mock UploadFile for testing"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.read = AsyncMock(return_value=content)
        mock_file.seek = AsyncMock()
        return mock_file
    
    @pytest.mark.asyncio
    async def test_upload_and_process_text_file(self):
        """Test uploading and processing a text file"""
        user_id = uuid4()
        test_content = b"This is a test log file\nERROR: Something went wrong"
        mock_file = self.create_mock_upload_file("test.log", test_content, "text/plain")
        
        # Mock S3 upload
        self.mock_s3_service.generate_key.return_value = "uploads/test.log"
        self.mock_s3_service.upload_file.return_value = "uploads/test.log"
        
        # Mock document creation
        mock_document = Document(
            id=uuid4(),
            filename="test.log",
            content_type="text/plain",
            s3_key="uploads/test.log",
            processed=False,
            meta_data={"user_id": str(user_id)},
            created_at=datetime.utcnow(),
            updated_at=None
        )
        self.mock_document_repository.create.return_value = mock_document
        
        # Mock background tasks
        mock_background_tasks = MagicMock()
        
        result = await self.file_service.upload_and_process_file(
            file=mock_file,
            user_id=user_id,
            background_tasks=mock_background_tasks,
            process_immediately=False
        )
        
        assert result.filename == "test.log"
        assert result.content_type == "text/plain"
        
        # Verify S3 upload was called
        self.mock_s3_service.upload_file.assert_called_once()
        
        # Verify document was created
        self.mock_document_repository.create.assert_called_once()
        
        # Verify background task was added
        mock_background_tasks.add_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_and_process_image_file(self):
        """Test uploading and processing an image file"""
        user_id = uuid4()
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        test_content = img_bytes.getvalue()
        
        mock_file = self.create_mock_upload_file("screenshot.png", test_content, "image/png")
        
        # Mock dependencies
        self.mock_s3_service.generate_key.return_value = "uploads/screenshot.png"
        self.mock_s3_service.upload_file.return_value = "uploads/screenshot.png"
        
        mock_document = Document(
            id=uuid4(),
            filename="screenshot.png",
            content_type="image/png",
            s3_key="uploads/screenshot.png",
            processed=False,
            meta_data={"user_id": str(user_id)},
            created_at=datetime.utcnow(),
            updated_at=None
        )
        self.mock_document_repository.create.return_value = mock_document
        
        mock_background_tasks = MagicMock()
        
        result = await self.file_service.upload_and_process_file(
            file=mock_file,
            user_id=user_id,
            background_tasks=mock_background_tasks,
            process_immediately=False
        )
        
        assert result.filename == "screenshot.png"
        assert result.content_type == "image/png"
    
    @pytest.mark.asyncio
    async def test_validate_file_unsupported_type(self):
        """Test file validation with unsupported file type"""
        mock_file = self.create_mock_upload_file("test.exe", b"binary content", "application/x-executable")
        
        with pytest.raises(UnsupportedFileTypeError):
            await self.file_service._validate_file(mock_file)
    
    @pytest.mark.asyncio
    async def test_validate_file_too_large(self):
        """Test file validation with file too large"""
        large_content = b"x" * (self.file_service.MAX_FILE_SIZE + 1)
        mock_file = self.create_mock_upload_file("large.txt", large_content, "text/plain")
        
        with pytest.raises(UnsupportedFileTypeError):
            await self.file_service._validate_file(mock_file)
    
    @pytest.mark.asyncio
    async def test_process_existing_file(self):
        """Test processing an existing file"""
        document_id = uuid4()
        test_content = b"Log file content\nERROR: Test error"
        
        # Mock document retrieval
        mock_document = Document(
            id=document_id,
            filename="test.log",
            content_type="text/plain",
            s3_key="uploads/test.log",
            processed=False,
            meta_data={},
            created_at=datetime.utcnow(),
            updated_at=None
        )
        self.mock_document_repository.get_by_id.return_value = mock_document
        
        # Mock S3 download
        self.mock_s3_service.download_file.return_value = test_content
        
        # Mock document update
        self.mock_document_repository.update.return_value = mock_document
        
        result = await self.file_service.process_existing_file(document_id)
        
        assert "processing_result" in result
        
        # Verify calls
        self.mock_document_repository.get_by_id.assert_called_with(document_id)
        self.mock_s3_service.download_file.assert_called_with("uploads/test.log")
        self.mock_document_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_file_processing_status(self):
        """Test getting file processing status"""
        document_id = uuid4()
        
        mock_document = Document(
            id=document_id,
            filename="test.txt",
            content_type="text/plain",
            s3_key="uploads/test.txt",
            processed=True,
            meta_data={"processing_result": {"status": "completed"}},
            created_at=datetime.utcnow(),
            updated_at=None
        )
        self.mock_document_repository.get_by_id.return_value = mock_document
        
        result = await self.file_service.get_file_processing_status(document_id)
        
        assert result["document_id"] == document_id
        assert result["filename"] == "test.txt"
        assert result["processed"] is True
        assert "processing_meta_data" in result
    
    @pytest.mark.asyncio
    async def test_delete_file(self):
        """Test file deletion"""
        document_id = uuid4()
        
        mock_document = Document(
            id=document_id,
            filename="test.txt",
            content_type="text/plain",
            s3_key="uploads/test.txt",
            processed=True,
            meta_data={},
            created_at=datetime.utcnow(),
            updated_at=None
        )
        self.mock_document_repository.get_by_id.return_value = mock_document
        self.mock_s3_service.delete_file.return_value = True
        self.mock_document_repository.delete.return_value = True
        
        result = await self.file_service.delete_file(document_id)
        
        assert result is True
        
        # Verify both S3 and database deletion
        self.mock_s3_service.delete_file.assert_called_with("uploads/test.txt")
        self.mock_document_repository.delete.assert_called_with(document_id)
    
    def test_is_log_file_detection(self):
        """Test log file detection logic"""
        # Test by filename
        assert self.file_service._is_log_file("error.log", "some content")
        assert self.file_service._is_log_file("debug.txt", "some content")
        assert not self.file_service._is_log_file("image.png", "some content")
        
        # Test by content
        log_content = "2024-01-15 10:30:45 ERROR Database connection failed"
        assert self.file_service._is_log_file("unknown.txt", log_content)
        
        non_log_content = "This is just regular text content"
        assert not self.file_service._is_log_file("unknown.txt", non_log_content)


class TestFileProcessingIntegration:
    """Integration tests for file processing workflows"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_log_processing(self):
        """Test complete log file processing workflow"""
        # This would test the complete workflow with real dependencies
        # For now, we'll create a simplified integration test
        
        log_content = """
2024-01-15 10:30:45 INFO Application started
2024-01-15 10:30:46 ERROR Database connection failed: Connection timeout
2024-01-15 10:30:47 FATAL Unable to start server
Traceback (most recent call last):
  File "server.py", line 123, in start_server
    connect_database()
  File "database.py", line 45, in connect_database
    raise ConnectionError("Database unavailable")
ConnectionError: Database unavailable
"""
        
        parser = LogFileParser()
        result = parser.parse_log_content(log_content)
        
        # Verify comprehensive parsing
        assert len(result["errors"]) >= 2  # ERROR and FATAL
        assert len(result["stack_traces"]) >= 1
        assert len(result["timestamps"]) >= 3
        assert result["meta_data"]["error_count"] >= 2
        assert "Database connection failed" in str(result["errors"])
        assert "Traceback" in str(result["stack_traces"])
    
    @pytest.mark.asyncio
    async def test_image_analysis_workflow(self):
        """Test image analysis workflow with mock AI provider"""
        mock_ai_provider = AsyncMock()
        mock_ai_provider.analyze_image.return_value = """
        This screenshot shows an error dialog with the message "File not found: config.xml".
        The error code displayed is ERR_404. The application appears to be a desktop
        application with file path C:\\Program Files\\MyApp\\config.xml visible.
        """
        
        analyzer = ImageAnalyzer(mock_ai_provider)
        
        # Create test image
        img = Image.new('RGB', (200, 100), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        test_image = img_bytes.getvalue()
        
        result = await analyzer.analyze_screenshot(test_image)
        
        # Verify analysis results
        assert "analysis" in result
        assert "extracted_text" in result
        assert "meta_data" in result
        
        # Verify pattern extraction
        patterns = result["extracted_text"]
        assert "ERR_404" in patterns["error_codes"]
        assert any("config.xml" in path for path in patterns["file_paths"])
        
        # Verify AI provider was called correctly
        mock_ai_provider.analyze_image.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
