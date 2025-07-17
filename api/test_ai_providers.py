#!/usr/bin/env python3
"""
Unit tests for AI provider implementations.
Tests the OpenAI provider with proper error handling, retry logic, and API key validation.
"""

import asyncio
import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any
from openai import AuthenticationError, RateLimitError as OpenAIRateLimitError

# Import the classes we're testing
from services.ai_providers import (
    OpenAIProvider, 
    AIProviderError, 
    APIKeyValidationError, 
    RateLimitError
)


class TestOpenAIProvider:
    """Test suite for OpenAI provider implementation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.provider = OpenAIProvider(api_key="test-api-key")
        self.test_messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        self.test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # JPEG header
        self.test_texts = ["Hello world", "This is a test"]
    
    def test_provider_initialization(self):
        """Test provider initialization with different parameters"""
        # Test with API key
        provider1 = OpenAIProvider(api_key="test-key")
        assert provider1.api_key == "test-key"
        assert provider1.base_url is None
        
        # Test with custom base URL
        provider2 = OpenAIProvider(api_key="test-key", base_url="https://custom.api.com")
        assert provider2.base_url == "https://custom.api.com"
        
        # Test without API key (should use environment)
        provider3 = OpenAIProvider()
        assert provider3.api_key is None
    
    def test_get_provider_name(self):
        """Test provider name method"""
        assert self.provider.get_provider_name() == "openai"
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self):
        """Test successful API key validation"""
        with patch('services.ai_providers.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            mock_client.models.list = AsyncMock()
            
            result = await self.provider.validate_api_key("valid-key")
            assert result is True
            mock_client.models.list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_api_key_invalid(self):
        """Test API key validation with invalid key"""
        with patch('services.ai_providers.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            mock_client.models.list = AsyncMock(side_effect=Exception("Authentication failed"))
            
            with pytest.raises(APIKeyValidationError):
                await self.provider.validate_api_key("invalid-key")
    
    @pytest.mark.asyncio
    async def test_validate_api_key_rate_limit(self):
        """Test API key validation with rate limit error"""
        with patch('services.ai_providers.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            mock_client.models.list = AsyncMock(side_effect=Exception("Rate limit exceeded"))
            
            with pytest.raises(APIKeyValidationError):  # Updated to expect correct exception
                await self.provider.validate_api_key("test-key")
    
    @pytest.mark.asyncio
    async def test_chat_completion_non_streaming(self):
        """Test non-streaming chat completion"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! I'm doing well, thank you."
        
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            result_generator = self.provider.chat_completion(
                messages=self.test_messages,
                stream=False
            )
            
            results = []
            async for chunk in result_generator:
                results.append(chunk)
            
            assert len(results) == 1
            assert results[0] == "Hello! I'm doing well, thank you."
            
            # Verify the API call
            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-4o-mini",
                messages=[{'role': 'user', 'content': 'Hello, how are you?'}],
                stream=False,
                temperature=0.7,
                max_tokens=None
            )
    
    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self):
        """Test streaming chat completion"""
        # Mock streaming response
        mock_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" there"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))])
        ]
        
        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk
        
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
            
            result_generator = self.provider.chat_completion(
                messages=self.test_messages,
                stream=True
            )
            
            results = []
            async for chunk in result_generator:
                results.append(chunk)
            
            assert results == ["Hello", " there", "!"]
    
    @pytest.mark.asyncio
    async def test_chat_completion_rate_limit_error(self):
        """Test chat completion with rate limit error"""
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )
            
            with pytest.raises(AIProviderError):
                result_generator = self.provider.chat_completion(
                    messages=self.test_messages
                )
                async for _ in result_generator:
                    pass
    
    @pytest.mark.asyncio
    async def test_chat_completion_general_error(self):
        """Test chat completion with general error"""
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API error")
            )
            
            with pytest.raises(AIProviderError):
                result_generator = self.provider.chat_completion(
                    messages=self.test_messages
                )
                async for _ in result_generator:
                    pass
    
    @pytest.mark.asyncio
    async def test_analyze_image_success(self):
        """Test successful image analysis"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This image shows an error dialog."
        
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            result = await self.provider.analyze_image(
                image_data=self.test_image_data,
                prompt="What do you see in this image?"
            )
            
            assert result == "This image shows an error dialog."
            
            # Verify the API call structure
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]['model'] == "gpt-4o-mini"
            assert call_args[1]['max_tokens'] == 1000
            
            # Check message structure
            messages = call_args[1]['messages']
            assert len(messages) == 1
            assert messages[0]['role'] == 'user'
            assert len(messages[0]['content']) == 2
            assert messages[0]['content'][0]['type'] == 'text'
            assert messages[0]['content'][1]['type'] == 'image_url'
    
    @pytest.mark.asyncio
    async def test_analyze_image_png_format(self):
        """Test image analysis with PNG format detection"""
        png_data = b'\x89PNG\r\n\x1a\n'  # PNG header
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PNG image analysis result"
        
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            result = await self.provider.analyze_image(
                image_data=png_data,
                prompt="Analyze this PNG"
            )
            
            assert result == "PNG image analysis result"
            
            # Verify PNG format was detected
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            image_url = messages[0]['content'][1]['image_url']['url']
            assert image_url.startswith('data:image/png;base64,')
    
    @pytest.mark.asyncio
    async def test_analyze_image_no_response(self):
        """Test image analysis with no response content"""
        mock_response = MagicMock()
        mock_response.choices = []
        
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            with pytest.raises(AIProviderError, match="No response content received"):
                await self.provider.analyze_image(
                    image_data=self.test_image_data,
                    prompt="Analyze this image"
                )
    
    @pytest.mark.asyncio
    async def test_analyze_image_rate_limit_error(self):
        """Test image analysis with rate limit error"""
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )
            
            with pytest.raises(AIProviderError):
                await self.provider.analyze_image(
                    image_data=self.test_image_data,
                    prompt="Analyze this image"
                )
    
    @pytest.mark.asyncio
    async def test_create_embeddings_success(self):
        """Test successful embedding creation"""
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6])
        ]
        
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            
            result = await self.provider.create_embeddings(self.test_texts)
            
            assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            
            # Verify API call
            mock_client.embeddings.create.assert_called_once_with(
                model="text-embedding-3-small",
                input=self.test_texts
            )
    
    @pytest.mark.asyncio
    async def test_create_embeddings_empty_input(self):
        """Test embedding creation with empty input"""
        result = await self.provider.create_embeddings([])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_create_embeddings_large_batch(self):
        """Test embedding creation with large batch (should be chunked)"""
        # Create a list larger than batch size (100)
        large_text_list = [f"Text {i}" for i in range(150)]
        
        mock_response1 = MagicMock()
        mock_response1.data = [MagicMock(embedding=[i/100, i/100, i/100]) for i in range(100)]
        
        mock_response2 = MagicMock()
        mock_response2.data = [MagicMock(embedding=[i/100, i/100, i/100]) for i in range(100, 150)]
        
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.embeddings.create = AsyncMock(side_effect=[mock_response1, mock_response2])
            
            result = await self.provider.create_embeddings(large_text_list)
            
            assert len(result) == 150
            assert mock_client.embeddings.create.call_count == 2
            
            # Verify batch sizes
            call_args_list = mock_client.embeddings.create.call_args_list
            assert len(call_args_list[0][1]['input']) == 100  # First batch
            assert len(call_args_list[1][1]['input']) == 50   # Second batch
    
    @pytest.mark.asyncio
    async def test_create_embeddings_rate_limit_error(self):
        """Test embedding creation with rate limit error"""
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.embeddings.create = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )
            
            with pytest.raises(AIProviderError):
                await self.provider.create_embeddings(self.test_texts)
    
    @pytest.mark.asyncio
    async def test_create_embeddings_general_error(self):
        """Test embedding creation with general error"""
        with patch.object(self.provider, '_client', create=True) as mock_client:
            mock_client.embeddings.create = AsyncMock(
                side_effect=Exception("API error")
            )
            
            with pytest.raises(AIProviderError):
                await self.provider.create_embeddings(self.test_texts)
    
    def test_client_property_caching(self):
        """Test that client property caches the OpenAI client"""
        provider = OpenAIProvider(api_key="test-key")
        
        # First access should create client
        client1 = provider.client
        assert client1 is not None
        
        # Second access should return same client
        client2 = provider.client
        assert client1 is client2


def run_tests():
    """Run all tests manually without pytest"""
    import sys
    import traceback
    
    test_instance = TestOpenAIProvider()
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    print("=== AI Provider Tests ===\n")
    
    for method_name in test_methods:
        try:
            print(f"Running {method_name}...")
            test_instance.setup_method()
            
            method = getattr(test_instance, method_name)
            if asyncio.iscoroutinefunction(method):
                asyncio.run(method())
            else:
                method()
            
            print(f"✓ {method_name} passed")
            passed += 1
            
        except Exception as e:
            print(f"✗ {method_name} failed: {str(e)}")
            traceback.print_exc()
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")


if __name__ == "__main__":
    # Check if pytest is available
    try:
        import pytest
        print("Running tests with pytest...")
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running manual tests...")
        run_tests()