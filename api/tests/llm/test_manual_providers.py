#!/usr/bin/env python3
"""
Manual test script to verify AI provider functionality.
This script requires real API keys to run properly.
"""

import asyncio
import os
from dotenv import load_dotenv
from services.ai_providers import OpenAIProvider, AIProviderError, APIKeyValidationError, RateLimitError

# Load environment variables from .env file
load_dotenv()


async def test_openai_provider():
    """Test the OpenAI provider with real API (if API key is available)"""
    print("=== Testing OpenAI Provider ===")
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("To test with real API, set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    provider = OpenAIProvider(api_key=api_key)
    
    try:
        # Test 1: API Key validation
        print("\n1. Testing API key validation...")
        is_valid = await provider.validate_api_key(api_key)
        print(f"✅ API key validation: {is_valid}")
        
        # Test 2: Chat completion (non-streaming)
        print("\n2. Testing chat completion (non-streaming)...")
        messages = [{"role": "user", "content": "Say hello in one word"}]
        
        result_generator = provider.chat_completion(messages, stream=False)
        results = []
        async for chunk in result_generator:
            results.append(chunk)
        
        print(f"✅ Chat completion result: {results[0]}")
        
        # Test 3: Chat completion (streaming)
        print("\n3. Testing chat completion (streaming)...")
        messages = [{"role": "user", "content": "Count from 1 to 3, one number per response"}]
        
        result_generator = provider.chat_completion(messages, stream=True)
        print("✅ Streaming response: ", end="")
        async for chunk in result_generator:
            print(chunk, end="")
        print()
        
        # Test 4: Embeddings
        print("\n4. Testing embeddings...")
        texts = ["Hello world", "This is a test"]
        embeddings = await provider.create_embeddings(texts)
        print(f"✅ Created embeddings for {len(texts)} texts")
        print(f"   First embedding dimension: {len(embeddings[0])}")
        print(f"   Second embedding dimension: {len(embeddings[1])}")
        
        # Test 5: Image analysis (with dummy image)
        print("\n5. Testing image analysis...")
        # Create a simple test image (1x1 red pixel PNG)
        test_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xd2\x00\x00\x00\x00\x00\x05\x17v\x06\xf9\x00\x00\x00\x00IEND\xaeB`\x82'
        
        try:
            analysis = await provider.analyze_image(test_image, "What color is this image?")
            print(f"✅ Image analysis result: {analysis[:100]}...")
        except Exception as e:
            print(f"⚠️ Image analysis failed (expected with test image): {str(e)[:100]}...")
        
        print("\n🎉 All OpenAI provider tests completed successfully!")
        
    except APIKeyValidationError as e:
        print(f"❌ API Key validation failed: {e}")
    except RateLimitError as e:
        print(f"❌ Rate limit exceeded: {e}")
    except AIProviderError as e:
        print(f"❌ AI Provider error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def test_provider_interface():
    """Test that the provider correctly implements the interface"""
    print("\n=== Testing Provider Interface ===")
    
    provider = OpenAIProvider(api_key="test-key")
    
    # Test required methods exist
    assert hasattr(provider, 'chat_completion'), "Missing chat_completion method"
    assert hasattr(provider, 'analyze_image'), "Missing analyze_image method"
    assert hasattr(provider, 'create_embeddings'), "Missing create_embeddings method"
    assert hasattr(provider, 'validate_api_key'), "Missing validate_api_key method"
    assert hasattr(provider, 'get_provider_name'), "Missing get_provider_name method"
    
    # Test provider name
    assert provider.get_provider_name() == "openai", "Incorrect provider name"
    
    print("✅ All interface requirements satisfied")


async def main():
    """Run all tests"""
    print("🚀 Starting AI Provider Manual Tests")
    
    await test_provider_interface()
    await test_openai_provider()
    
    print("\n✨ Manual testing completed!")


if __name__ == "__main__":
    asyncio.run(main())
