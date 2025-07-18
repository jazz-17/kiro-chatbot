from typing import Union

from fastapi import Depends, FastAPI, HTTPException

from database.base import get_db
from models.user import UserCreate, UserResponse
from sqlalchemy.ext.asyncio import AsyncConnection
from routers import auth_router, chat_router, files_router

app = FastAPI(
    title="Kiro Chatbot API",
    description="AI-powered technical support chatbot with multi-modal file processing",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {
        "message": "Kiro Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/v1/auth",
            "chat": "/api/v1/chat", 
            "files": "/api/v1/files"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "kiro-chatbot-api",
        "timestamp": "2024-01-15T10:30:00Z"
    }


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    connection: AsyncConnection = Depends(get_db)
):
    """Create a new user"""
    try:
        service = UserService(connection)
        user = await service.create_user(user_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
