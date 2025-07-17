"""AI Provider implementations"""

import asyncio
import base64
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from io import BytesIO

import httpx
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .base import AIProvider


logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    pass


class APIKeyValidationError(AIProviderError):
    """Raised when API key validation fails"""
    pass


class RateLimitError(AIProviderError):
    """Raised when rate limit is exceeded"""
    pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation with chat completion, image analysis, and embeddings"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key. If None, will use environment variable
            base_url: Custom base URL for OpenAI API (for compatible services)
        """
        self.api_key = api_key
        self.base_url = base_url
        self._client: Optional[AsyncOpenAI] = None
        
    @property
    def client(self) -> AsyncOpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client
    
    def get_provider_name(self) -> str:
        """Get the name of the provider"""
        return "openai"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    )
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate OpenAI API key by making a simple API call
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if the API key is valid, False otherwise
            
        Raises:
            APIKeyValidationError: If validation fails due to invalid key
        """
        try:
            # Create a temporary client with the provided API key
            temp_client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)
            
            # Make a simple API call to validate the key
            await temp_client.models.list()
            return True
            
        except Exception as e:
            error_message = str(e).lower()
            if "invalid api key" in error_message or "unauthorized" in error_message:
                raise APIKeyValidationError(f"Invalid API key: {str(e)}")
            elif "rate limit" in error_message:
                raise RateLimitError(f"Rate limit exceeded: {str(e)}")
            else:
                logger.error(f"API key validation failed: {str(e)}")
                return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate chat completion response with streaming support
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters for OpenAI API
            
        Yields:
            Response chunks if streaming, otherwise yields complete response
            
        Raises:
            AIProviderError: If the API call fails
            RateLimitError: If rate limit is exceeded
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            if stream:
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                if response.choices and response.choices[0].message.content:
                    yield response.choices[0].message.content
                    
        except Exception as e:
            error_message = str(e).lower()
            if "rate limit" in error_message:
                raise RateLimitError(f"Rate limit exceeded: {str(e)}")
            else:
                raise AIProviderError(f"Chat completion failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    )
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Analyze image content using OpenAI's vision capabilities
        
        Args:
            image_data: Raw image bytes
            prompt: Text prompt for image analysis
            model: OpenAI model to use (must support vision)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters for OpenAI API
            
        Returns:
            Analysis result as string
            
        Raises:
            AIProviderError: If the API call fails
            RateLimitError: If rate limit is exceeded
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image format (simple detection)
            image_format = "jpeg"  # Default
            if image_data.startswith(b'\x89PNG'):
                image_format = "png"
            elif image_data.startswith(b'GIF'):
                image_format = "gif"
            elif image_data.startswith(b'\xff\xd8'):
                image_format = "jpeg"
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                **kwargs
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                raise AIProviderError("No response content received from image analysis")
                
        except Exception as e:
            error_message = str(e).lower()
            if "rate limit" in error_message:
                raise RateLimitError(f"Rate limit exceeded: {str(e)}")
            else:
                raise AIProviderError(f"Image analysis failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    )
    async def create_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small",
        **kwargs
    ) -> List[List[float]]:
        """Create vector embeddings for text chunks
        
        Args:
            texts: List of text strings to embed
            model: OpenAI embedding model to use
            **kwargs: Additional parameters for OpenAI API
            
        Returns:
            List of embedding vectors (list of floats)
            
        Raises:
            AIProviderError: If the API call fails
            RateLimitError: If rate limit is exceeded
        """
        if not texts:
            return []
            
        try:
            # OpenAI has a limit on batch size, so we'll process in chunks
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await self.client.embeddings.create(
                    model=model,
                    input=batch,
                    **kwargs
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            error_message = str(e).lower()
            if "rate limit" in error_message:
                raise RateLimitError(f"Rate limit exceeded: {str(e)}")
            else:
                raise AIProviderError(f"Embedding creation failed: {str(e)}")