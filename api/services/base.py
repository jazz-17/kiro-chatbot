from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from uuid import UUID


class BaseService(ABC):
    """Base service interface for all services"""
    pass


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate chat completion response with optional streaming"""
        pass
    
    @abstractmethod
    async def analyze_image(self, image_data: bytes, prompt: str) -> str:
        """Analyze image content for multi-modal processing"""
        pass
    
    @abstractmethod
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create vector embeddings for text chunks"""
        pass
    
    @abstractmethod
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate API key for the provider"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the provider"""
        pass


class VectorDatabase(ABC):
    """Abstract base class for vector database operations"""
    
    @abstractmethod
    async def store_embedding(
        self, 
        content: str, 
        embedding: List[float], 
        metadata: Dict[str, Any]
    ) -> str:
        """Store content with its embedding"""
        pass
    
    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.7,
        filter: Dict[str, Any] = None # type: ignore
    ) -> List[Dict[str, Any]]:
        """Perform similarity search with optional metadata filtering"""
        pass
        
    @abstractmethod
    async def delete_embedding(self, embedding_id: str) -> bool:
        """Delete an embedding by ID"""
        pass
    
      
    @abstractmethod
    async def store_embeddings_batch(
        self,
        contents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> List[str] | None:
        """Store a batch of contents with their embeddings"""
        pass

        