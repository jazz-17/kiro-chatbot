from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import UUID

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for CRUD operations"""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        pass
    
    @abstractmethod
    async def update(self, entity_id: UUID, update_data: Dict[str, Any]) -> Optional[T]:
        """Update entity by ID"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID"""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """Check if entity exists"""
        pass


class UserRepository(BaseRepository):
    """Repository interface for user operations"""
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Any]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        pass


class ConversationRepository(BaseRepository):
    """Repository interface for conversation operations"""
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get conversations by user ID"""
        pass
    
    @abstractmethod
    async def add_message(self, conversation_id: UUID, message: Any) -> Any:
        """Add message to conversation"""
        pass
    
    @abstractmethod
    async def get_messages(self, conversation_id: UUID, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get messages for a conversation"""
        pass