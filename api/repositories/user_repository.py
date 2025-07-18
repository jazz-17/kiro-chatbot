"""
SQLAlchemy Core implementation of UserRepository.
This replaces the ORM-based repository with explicit SQL operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import select, insert, update, delete, and_, func
from sqlalchemy.exc import IntegrityError

from repositories.base import UserRepository
from database.tables import users_table
from models.user import User


class SQLAlchemyUserRepository(UserRepository[User]):
    """SQLAlchemy Core implementation of UserRepository"""
    
    def __init__(self, connection: AsyncConnection):
        self.connection = connection
    
    async def create(self, entity: User) -> User:
        """Create a new user"""
        try:
            # Prepare insert values
            insert_values = {
                "id": entity.id or uuid4(),
                "email": entity.email,
                "password_hash": entity.password_hash,
                "encrypted_api_keys": entity.encrypted_api_keys,
                "preferences": entity.preferences,
                "created_at": entity.created_at or datetime.utcnow(),
                "updated_at": entity.updated_at
            }
            
            # Execute insert and get the result
            stmt = insert(users_table).values(**insert_values).returning(users_table)
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return User(
                    id=row.id,
                    email=row.email,
                    password_hash=row.password_hash,
                    encrypted_api_keys=row.encrypted_api_keys,
                    preferences=row.preferences,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            else:
                raise ValueError("Failed to create user")
                
        except IntegrityError as e:
            raise ValueError(f"User creation failed: {str(e)}")
    
    async def get_by_id(self, entity_id: UUID) -> Optional[User]:
        """Get user by ID"""
        stmt = select(users_table).where(users_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        row = result.fetchone()
        
        if row:
            return User(
                id=row.id,
                email=row.email,
                password_hash=row.password_hash,
                encrypted_api_keys=row.encrypted_api_keys,
                preferences=row.preferences,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        return None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        stmt = (
            select(users_table)
            .offset(skip)
            .limit(limit)
            .order_by(users_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            User(
                id=row.id,
                email=row.email,
                password_hash=row.password_hash,
                encrypted_api_keys=row.encrypted_api_keys,
                preferences=row.preferences,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]
    
    async def update(self, entity_id: UUID, update_data: Dict[str, Any]) -> Optional[User]:
        """Update user by ID"""
        try:
            # Add updated_at timestamp
            update_data = {**update_data, "updated_at": datetime.utcnow()}
            
            stmt = (
                update(users_table)
                .where(users_table.c.id == entity_id)
                .values(**update_data)
                .returning(users_table)
            )
            result = await self.connection.execute(stmt)
            row = result.fetchone()
            
            if row:
                return User(
                    id=row.id,
                    email=row.email,
                    password_hash=row.password_hash,
                    encrypted_api_keys=row.encrypted_api_keys,
                    preferences=row.preferences,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            return None
            
        except IntegrityError as e:
            raise ValueError(f"User update failed: {str(e)}")
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete user by ID"""
        stmt = delete(users_table).where(users_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.rowcount > 0
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if user exists"""
        stmt = select(users_table.c.id).where(users_table.c.id == entity_id)
        result = await self.connection.execute(stmt)
        return result.fetchone() is not None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(users_table).where(users_table.c.email == email)
        result = await self.connection.execute(stmt)
        row = result.fetchone()
        
        if row:
            return User(
                id=row.id,
                email=row.email,
                password_hash=row.password_hash,
                encrypted_api_keys=row.encrypted_api_keys,
                preferences=row.preferences,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        return None
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        stmt = select(users_table.c.id).where(users_table.c.email == email)
        result = await self.connection.execute(stmt)
        return result.fetchone() is not None
    
    async def update_api_keys(self, user_id: UUID, encrypted_api_keys: Dict[str, str]) -> Optional[User]:
        """Update user's encrypted API keys"""
        return await self.update(user_id, {"encrypted_api_keys": encrypted_api_keys})
    
    async def update_preferences(self, user_id: UUID, preferences: Dict[str, Any]) -> Optional[User]:
        """Update user's preferences"""
        return await self.update(user_id, {"preferences": preferences})
    
    async def get_user_count(self) -> int:
        """Get total number of users"""
        stmt = select(func.count(users_table.c.id))
        result = await self.connection.execute(stmt)
        return result.scalar() or 0
    
    async def get_users_created_after(self, date: datetime) -> List[User]:
        """Get users created after a specific date"""
        stmt = (
            select(users_table)
            .where(users_table.c.created_at >= date)
            .order_by(users_table.c.created_at.desc())
        )
        result = await self.connection.execute(stmt)
        rows = result.fetchall()
        
        return [
            User(
                id=row.id,
                email=row.email,
                password_hash=row.password_hash,
                encrypted_api_keys=row.encrypted_api_keys,
                preferences=row.preferences,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]