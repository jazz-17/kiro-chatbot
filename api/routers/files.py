"""
File management API router

This module provides FastAPI endpoints for file upload, processing, and management.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from models.document import DocumentResponse
from services.file_service import FileService, FileProcessingError, UnsupportedFileTypeError
from services.ai_providers import OpenAIProvider
from services.file_service import S3StorageService
from api.repositories.document_repository import DocumentRepository
from database.base import get_async_connection
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


async def get_file_service(
    connection: AsyncConnection = Depends(get_async_connection)
) -> FileService:
    """Dependency to get FileService instance"""
    # Initialize dependencies
    ai_provider = OpenAIProvider()  # Should use proper config/DI
    s3_service = S3StorageService(
        bucket_name="kiro-chatbot-files",  # Should come from config
        endpoint_url=None,  # For local development
    )
    document_repository = DocumentRepository(connection)
    
    return FileService(
        ai_provider=ai_provider,
        s3_service=s3_service,
        document_repository=document_repository
    )


# TODO: Add proper authentication middleware
async def get_current_user_id() -> UUID:
    """Get current user ID from authentication context"""
    # This should be replaced with proper JWT token validation
    from uuid import uuid4
    return uuid4()  # Placeholder for development


@router.post("/upload", response_model=DocumentResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    process_immediately: bool = Form(False),
    user_id: UUID = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload a file for processing
    
    - **file**: The file to upload (images, logs, text files, documents)
    - **process_immediately**: Whether to process the file immediately (default: False)
    
    Returns the created document record with upload information.
    """
    try:
        document = await file_service.upload_and_process_file(
            file=file,
            user_id=user_id,
            background_tasks=background_tasks,
            process_immediately=process_immediately
        )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            content_type=document.content_type,
            s3_key=document.s3_key,
            processed=document.processed,
            meta_data=document.meta_data,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        
    except UnsupportedFileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file upload"
        )


@router.get("/{file_id}", response_model=DocumentResponse)
async def get_file_info(
    file_id: UUID,
    file_service: FileService = Depends(get_file_service)
):
    """
    Get file information by ID
    
    Returns detailed information about the uploaded file including processing status.
    """
    try:
        status_info = await file_service.get_file_processing_status(file_id)
        
        # Get the full document for response
        document = await file_service.document_repository.get_by_id(file_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            content_type=document.content_type,
            s3_key=document.s3_key,
            processed=document.processed,
            meta_data=document.meta_data,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting file info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/{file_id}/status")
async def get_file_processing_status(
    file_id: UUID,
    file_service: FileService = Depends(get_file_service)
):
    """
    Get the processing status of a file
    
    Returns processing status, meta_data, and any extracted information.
    """
    try:
        status_info = await file_service.get_file_processing_status(file_id)
        return status_info
        
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting processing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/{file_id}/process")
async def process_file(
    file_id: UUID,
    file_service: FileService = Depends(get_file_service)
):
    """
    Manually trigger processing of an uploaded file
    
    Useful for reprocessing files or processing files that were uploaded without immediate processing.
    """
    try:
        processing_result = await file_service.process_existing_file(file_id)
        return {
            "message": "File processing completed",
            "file_id": file_id,
            "processing_result": processing_result
        }
        
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error processing file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file processing"
        )


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    file_service: FileService = Depends(get_file_service)
):
    """
    Download the original file content
    
    Returns the file as a streaming response with appropriate headers.
    """
    try:
        # Get document info
        document = await file_service.document_repository.get_by_id(file_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Get file content from S3
        file_content = await file_service.s3_service.download_file(document.s3_key)
        
        # Create streaming response
        def generate_file():
            yield file_content
        
        return StreamingResponse(
            generate_file(),
            media_type=document.content_type,
            headers={
                "Content-Disposition": f"attachment; filename={document.filename}",
                "Content-Length": str(len(file_content))
            }
        )
        
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error downloading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file download"
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    file_service: FileService = Depends(get_file_service)
):
    """
    Delete a file and all associated data
    
    This removes the file from storage and all database records.
    """
    try:
        success = await file_service.delete_file(file_id)
        
        if success:
            return {"message": "File deleted successfully", "file_id": file_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file deletion"
        )


@router.get("/")
async def list_files(
    skip: int = 0,
    limit: int = 100,
    processed_only: bool = False,
    user_id: UUID = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service)
):
    """
    List files uploaded by the current user
    
    - **skip**: Number of files to skip for pagination
    - **limit**: Maximum number of files to return
    - **processed_only**: Only return files that have been processed
    """
    try:
        # Get documents from repository
        documents = await file_service.document_repository.get_all(skip=skip, limit=limit)
        
        # Filter by processed status if requested
        if processed_only:
            documents = [doc for doc in documents if doc.processed]
        
        # Convert to response format
        responses = [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                content_type=doc.content_type,
                s3_key=doc.s3_key,
                processed=doc.processed,
                meta_data=doc.meta_data,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
        
        return {
            "files": responses,
            "total": len(responses),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Unexpected error listing files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing files"
        )


@router.post("/bulk-upload")
async def bulk_upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    process_immediately: bool = Form(False),
    user_id: UUID = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload multiple files at once
    
    - **files**: List of files to upload
    - **process_immediately**: Whether to process all files immediately
    
    Returns information about all uploaded files.
    """
    try:
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                document = await file_service.upload_and_process_file(
                    file=file,
                    user_id=user_id,
                    background_tasks=background_tasks,
                    process_immediately=process_immediately
                )
                
                uploaded_files.append(DocumentResponse(
                    id=document.id,
                    filename=document.filename,
                    content_type=document.content_type,
                    s3_key=document.s3_key,
                    processed=document.processed,
                    meta_data=document.meta_data,
                    created_at=document.created_at,
                    updated_at=document.updated_at
                ))
                
            except (UnsupportedFileTypeError, FileProcessingError) as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "uploaded_files": uploaded_files,
            "errors": errors,
            "total_uploaded": len(uploaded_files),
            "total_errors": len(errors)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error during bulk upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during bulk upload"
        )
