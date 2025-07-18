"""
File Processing Service

This module implements the FileService for handling multi-modal file uploads,
log file parsing, image analysis, S3 storage, and background task processing.
"""

import asyncio
import json
import logging
import re
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

import aiofiles
from fastapi import BackgroundTasks, UploadFile
from PIL import Image

from .ai_providers import OpenAIProvider
from .base import BaseService
from models.document import Document, DocumentCreate
from api.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Base exception for file processing errors"""

    pass


class UnsupportedFileTypeError(FileProcessingError):
    """Raised when file type is not supported"""

    pass


class S3StorageError(FileProcessingError):
    """Raised when S3 storage operations fail"""

    pass


class LogParsingError(FileProcessingError):
    """Raised when log parsing fails"""

    pass


class ImageAnalysisError(FileProcessingError):
    """Raised when image analysis fails"""

    pass


class LogFileParser:
    """Parser for extracting structured information from log files"""

    # Common error patterns
    ERROR_PATTERNS = [
        r"ERROR\s*:?\s*(.*?)(?:\n|$)",
        r"FATAL\s*:?\s*(.*?)(?:\n|$)",
        r"Exception\s*:?\s*(.*?)(?:\n|$)",
        r"Error\s*:?\s*(.*?)(?:\n|$)",
        r"\[ERROR\]\s*(.*?)(?:\n|$)",
        r"CRITICAL\s*:?\s*(.*?)(?:\n|$)",
    ]

    # Stack trace patterns
    STACK_TRACE_PATTERNS = [
        r"Traceback \(most recent call last\):(.*?)(?=\n\S|\n$)",
        r"at\s+[\w\.]+\([^)]+\)",
        r"^\s+at\s+.*$",
        r"Caused by:.*",
    ]

    # Timestamp patterns
    TIMESTAMP_PATTERNS = [
        r"\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
        r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}",
        r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}",
    ]

    # Log level patterns
    LOG_LEVEL_PATTERNS = [
        r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL|TRACE)\b",
    ]

    def parse_log_content(self, content: str) -> Dict[str, Any]:
        """Parse log content and extract structured information"""
        try:
            parsed_data = {
                "errors": self._extract_errors(content),
                "stack_traces": self._extract_stack_traces(content),
                "timestamps": self._extract_timestamps(content),
                "log_levels": self._extract_log_levels(content),
                "summary": self._generate_summary(content),
                "meta_data": {
                    "line_count": len(content.split("\n")),
                    "error_count": 0,
                    "warning_count": 0,
                    "parsed_at": datetime.utcnow().isoformat(),
                },
            }

            # Count log levels
            for level_info in parsed_data["log_levels"]:
                level = level_info["level"].upper()
                if level in ["ERROR", "FATAL", "CRITICAL"]:
                    parsed_data["meta_data"]["error_count"] += 1
                elif level in ["WARN", "WARNING"]:
                    parsed_data["meta_data"]["warning_count"] += 1

            return parsed_data

        except Exception as e:
            logger.error(f"Failed to parse log content: {e}")
            raise LogParsingError(f"Failed to parse log content: {e}")

    def _extract_errors(self, content: str) -> List[Dict[str, str]]:
        """Extract error messages from log content"""
        errors = []
        for pattern in self.ERROR_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                errors.append(
                    {
                        "message": match.group(1).strip(),
                        "pattern": pattern,
                        "line_number": content[: match.start()].count("\n") + 1,
                    }
                )
        return errors

    def _extract_stack_traces(self, content: str) -> List[Dict[str, str]]:
        """Extract stack traces from log content"""
        stack_traces = []
        for pattern in self.STACK_TRACE_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                stack_traces.append(
                    {
                        "trace": match.group(0).strip(),
                        "line_number": content[: match.start()].count("\n") + 1,
                    }
                )
        return stack_traces

    def _extract_timestamps(self, content: str) -> List[Dict[str, str]]:
        """Extract timestamps from log content"""
        timestamps = []
        for pattern in self.TIMESTAMP_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                timestamps.append(
                    {
                        "timestamp": match.group(0),
                        "line_number": content[: match.start()].count("\n") + 1,
                    }
                )
        return timestamps[:10]  # Limit to first 10 timestamps

    def _extract_log_levels(self, content: str) -> List[Dict[str, str]]:
        """Extract log levels from content"""
        levels = []
        for pattern in self.LOG_LEVEL_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                levels.append(
                    {
                        "level": match.group(1).upper(),
                        "line_number": content[: match.start()].count("\n") + 1,
                    }
                )
        return levels

    def _generate_summary(self, content: str) -> str:
        """Generate a summary of the log content"""
        lines = content.split("\n")
        total_lines = len(lines)

        # Count different log levels
        error_count = len(
            re.findall(r"\b(ERROR|FATAL|CRITICAL)\b", content, re.IGNORECASE)
        )
        warning_count = len(re.findall(r"\b(WARN|WARNING)\b", content, re.IGNORECASE))

        summary = f"Log file with {total_lines} lines"
        if error_count > 0:
            summary += f", {error_count} errors"
        if warning_count > 0:
            summary += f", {warning_count} warnings"

        return summary


class ImageAnalyzer:
    """Analyzer for extracting information from images using multi-modal AI"""

    def __init__(self, ai_provider: OpenAIProvider):
        self.ai_provider = ai_provider

    async def analyze_screenshot(
        self,
        image_data: bytes,
        context: str = "Analyze this screenshot for error messages, UI elements, and technical information",
    ) -> Dict[str, Any]:
        """Analyze screenshot for error messages and UI elements"""
        try:
            # Validate image format
            self._validate_image(image_data)

            # Analyze with AI
            analysis_prompt = f"""
            {context}
            
            Please analyze this image and extract:
            1. Any error messages or error dialogs visible
            2. Application or system information shown
            3. UI state and relevant context
            4. Technical details like file paths, URLs, or code snippets
            5. Overall description of what's happening in the image
            
            Provide the analysis in a structured format.
            """

            analysis_result = await self.ai_provider.analyze_image(
                image_data=image_data, prompt=analysis_prompt, max_tokens=1000
            )

            return {
                "analysis": analysis_result,
                "extracted_text": self._extract_text_patterns(analysis_result),
                "meta_data": {
                    "image_size": len(image_data),
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "ai_model": "gpt-4o-mini",
                },
            }

        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            raise ImageAnalysisError(f"Failed to analyze image: {e}")

    def _validate_image(self, image_data: bytes) -> None:
        """Validate that the data is a valid image"""
        try:
            with Image.open(BytesIO(image_data)) as img:
                # Basic validation - ensure it's a valid image
                img.verify()
        except Exception as e:
            raise ImageAnalysisError(f"Invalid image data: {e}")

    def _extract_text_patterns(self, analysis: str) -> Dict[str, List[str]]:
        """Extract specific patterns from analysis text"""
        patterns = {
            "error_codes": re.findall(
                r"\b(?:error|err)\s*(?:code\s*)?[:=]?\s*(\w+|\d+)",
                analysis,
                re.IGNORECASE,
            ),
            "file_paths": re.findall(
                r"[A-Za-z]:[\\\/](?:[^\\\/\s]+[\\\/])*[^\\\/\s]*|\/(?:[^\/\s]+\/)*[^\/\s]*",
                analysis,
            ),
            "urls": re.findall(r"https?://[^\s]+", analysis),
            "exceptions": re.findall(r"\b\w*Exception\b|\b\w*Error\b", analysis),
        }
        return patterns


class S3StorageService:
    """S3-compatible storage service for file persistence"""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "us-east-1",
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        # Note: In a real implementation, you would use boto3 or similar
        # For now, we'll simulate S3 storage with local file system
        self.storage_path = Path("/tmp/kiro_file_storage")
        self.storage_path.mkdir(exist_ok=True)

    async def upload_file(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        meta_data: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload file to S3-compatible storage"""
        try:
            # Simulate S3 upload with local file system
            file_path = self.storage_path / key
            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_data)

            logger.info(f"File uploaded to {key}")
            return key

        except Exception as e:
            logger.error(f"Failed to upload file {key}: {e}")
            raise S3StorageError(f"Failed to upload file: {e}")

    async def download_file(self, key: str) -> bytes:
        """Download file from S3-compatible storage"""
        try:
            file_path = self.storage_path / key
            if not file_path.exists():
                raise S3StorageError(f"File not found: {key}")

            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()

        except Exception as e:
            logger.error(f"Failed to download file {key}: {e}")
            raise S3StorageError(f"Failed to download file: {e}")

    async def delete_file(self, key: str) -> bool:
        """Delete file from S3-compatible storage"""
        try:
            file_path = self.storage_path / key
            if file_path.exists():
                file_path.unlink()
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete file {key}: {e}")
            raise S3StorageError(f"Failed to delete file: {e}")

    def generate_key(self, filename: str, user_id: Optional[UUID] = None) -> str:
        """Generate unique S3 key for file"""
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = uuid4().hex[:8]

        if user_id:
            return f"uploads/{user_id}/{timestamp}/{unique_id}_{filename}"
        else:
            return f"uploads/anonymous/{timestamp}/{unique_id}_{filename}"


class FileService(BaseService):
    """Service for handling multi-modal file uploads and processing"""

    SUPPORTED_IMAGE_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    }

    SUPPORTED_TEXT_TYPES = {"text/plain", "text/log", "application/json", "text/csv"}

    SUPPORTED_DOCUMENT_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    def __init__(
        self,
        ai_provider: OpenAIProvider,
        s3_service: S3StorageService,
        document_repository: DocumentRepository,
    ):
        self.ai_provider = ai_provider
        self.s3_service = s3_service
        self.document_repository = document_repository
        self.log_parser = LogFileParser()
        self.image_analyzer = ImageAnalyzer(ai_provider)

    async def upload_and_process_file(
        self,
        file: UploadFile,
        user_id: UUID,
        background_tasks: BackgroundTasks,
        process_immediately: bool = False,
    ) -> Document:
        """Upload file and optionally process it immediately or in background"""
        try:
            # Validate file
            await self._validate_file(file)

            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer

            file_content_type = file.content_type or "application/octet-stream"
            if not file.filename:
                raise UnsupportedFileTypeError("Filename is required")

            # Generate S3 key
            s3_key = self.s3_service.generate_key(file.filename, user_id)

            # Upload to S3
            await self.s3_service.upload_file(
                file_data=file_content,
                key=s3_key,
                content_type=file_content_type,
                meta_data={
                    "original_filename": file.filename,
                    "uploaded_by": str(user_id),
                    "upload_timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Create document record
            document_create = DocumentCreate(
                filename=file.filename,
                content_type=file_content_type,
                s3_key=s3_key,
                meta_data={
                    "user_id": str(user_id),
                    "file_size": len(file_content),
                    "upload_timestamp": datetime.utcnow().isoformat(),
                },
            )

            document = await self.document_repository.create(
                Document(**document_create.dict())
            )

            # Process file
            if process_immediately:
                processing_result = await self._process_file_content(
                    document, file_content
                )
                # Update document with processing results
                await self.document_repository.update(
                    document.id,
                    {
                        "processed": True,
                        "meta_data": {**document.meta_data, **processing_result},
                    },
                )
            else:
                # Schedule background processing
                background_tasks.add_task(
                    self._background_process_file, document.id, file_content
                )

            logger.info(f"File uploaded successfully: {document.id}")
            return document

        except Exception as e:
            logger.error(f"Failed to upload and process file: {e}")
            raise FileProcessingError(f"Failed to upload and process file: {e}")

    async def process_existing_file(self, document_id: UUID) -> Dict[str, Any]:
        """Process an existing file by document ID"""
        try:
            # Get document
            document = await self.document_repository.get_by_id(document_id)
            if not document:
                raise FileProcessingError(f"Document not found: {document_id}")

            # Download file content
            file_content = await self.s3_service.download_file(document.s3_key)

            # Process content
            processing_result = await self._process_file_content(document, file_content)

            # Update document
            await self.document_repository.update(
                document_id,
                {
                    "processed": True,
                    "meta_data": {**document.meta_data, **processing_result},
                },
            )

            return processing_result

        except Exception as e:
            logger.error(f"Failed to process existing file {document_id}: {e}")
            raise FileProcessingError(f"Failed to process existing file: {e}")

    async def get_file_processing_status(self, document_id: UUID) -> Dict[str, Any]:
        """Get the processing status of a file"""
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise FileProcessingError(f"Document not found: {document_id}")

        return {
            "document_id": document.id,
            "filename": document.filename,
            "processed": document.processed,
            "upload_time": document.created_at,
            "processing_meta_data": document.meta_data.get("processing_result", {}),
        }

    async def delete_file(self, document_id: UUID) -> bool:
        """Delete a file and its associated data"""
        try:
            document = await self.document_repository.get_by_id(document_id)
            if not document:
                return False

            # Delete from S3
            await self.s3_service.delete_file(document.s3_key)

            # Delete from database
            await self.document_repository.delete(document_id)

            logger.info(f"File deleted successfully: {document_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {document_id}: {e}")
            raise FileProcessingError(f"Failed to delete file: {e}")

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        if not file.filename:
            raise UnsupportedFileTypeError("Filename is required")

        if not file.content_type:
            raise UnsupportedFileTypeError("Content type is required")

        # Check file size
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer

        if len(file_content) > self.MAX_FILE_SIZE:
            raise UnsupportedFileTypeError(
                f"File too large. Max size: {self.MAX_FILE_SIZE} bytes"
            )

        # Check content type
        supported_types = (
            self.SUPPORTED_IMAGE_TYPES
            | self.SUPPORTED_TEXT_TYPES
            | self.SUPPORTED_DOCUMENT_TYPES
        )

        if file.content_type not in supported_types:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: {file.content_type}. "
                f"Supported types: {', '.join(supported_types)}"
            )

    async def _process_file_content(
        self, document: Document, file_content: bytes
    ) -> Dict[str, Any]:
        """Process file content based on its type"""
        try:
            processing_result = {
                "processing_timestamp": datetime.utcnow().isoformat(),
                "content_type": document.content_type,
                "file_size": len(file_content),
            }

            if document.content_type in self.SUPPORTED_IMAGE_TYPES:
                # Process image
                image_result = await self.image_analyzer.analyze_screenshot(
                    file_content
                )
                processing_result.update({"type": "image", "analysis": image_result})

            elif document.content_type in self.SUPPORTED_TEXT_TYPES:
                # Process text/log file
                text_content = file_content.decode("utf-8", errors="ignore")

                if self._is_log_file(document.filename, text_content):
                    log_result = self.log_parser.parse_log_content(text_content)
                    processing_result.update({"type": "log", "parsed_data": log_result})
                else:
                    processing_result.update(
                        {
                            "type": "text",
                            "content_preview": text_content[:1000],
                            "line_count": len(text_content.split("\n")),
                            "character_count": len(text_content),
                        }
                    )

            else:
                # For other document types, store basic meta_data
                processing_result.update({"type": "document", "status": "stored"})

            return {"processing_result": processing_result}

        except Exception as e:
            logger.error(f"Failed to process file content: {e}")
            return {
                "processing_result": {
                    "error": str(e),
                    "processing_timestamp": datetime.utcnow().isoformat(),
                    "status": "failed",
                }
            }

    async def _background_process_file(
        self, document_id: UUID, file_content: bytes
    ) -> None:
        """Background task for processing files"""
        try:
            document = await self.document_repository.get_by_id(document_id)
            if not document:
                logger.error(
                    f"Document not found for background processing: {document_id}"
                )
                return

            processing_result = await self._process_file_content(document, file_content)

            await self.document_repository.update(
                document_id,
                {
                    "processed": True,
                    "meta_data": {**document.meta_data, **processing_result},
                },
            )

            logger.info(f"Background processing completed for document: {document_id}")

        except Exception as e:
            logger.error(
                f"Background processing failed for document {document_id}: {e}"
            )
            # Update document with error status
            try:
                await self.document_repository.update(
                    document_id,
                    {
                        "meta_data": {
                            "processing_error": str(e),
                            "processing_timestamp": datetime.utcnow().isoformat(),
                        }
                    },
                )
            except Exception as update_error:
                logger.error(
                    f"Failed to update document with error status: {update_error}"
                )

    def _is_log_file(self, filename: str, content: str) -> bool:
        """Determine if a file is a log file based on filename and content"""
        # Check filename patterns
        log_extensions = [".log", ".txt", ".out"]
        log_keywords = ["log", "error", "debug", "trace", "audit"]

        filename_lower = filename.lower()

        # Check extension
        if any(filename_lower.endswith(ext) for ext in log_extensions):
            # Check for log keywords in filename
            if any(keyword in filename_lower for keyword in log_keywords):
                return True

        # Check content patterns
        log_indicators = [
            r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b",
            r"\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}",
            r"Exception\s*:",
            r"Traceback\s*\(",
            r"\[ERROR\]",
            r"Stack trace",
        ]

        for pattern in log_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False
