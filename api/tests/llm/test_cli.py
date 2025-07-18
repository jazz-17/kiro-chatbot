#!/usr/bin/env python3
"""
Simple CLI test script for the AI provider.
Usage: python test_cli.py [command]

Commands:
  validate    - Test API key validation
  chat        - Test chat completion
  stream      - Test streaming chat
  embed       - Test embeddings
  image       - Test image analysis
  all         - Run all tests
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from services.ai_providers import OpenAIProvider, AIProviderError, APIKeyValidationError, RateLimitError

# Load environment variables
load_dotenv()


async def test_validation():
    """Test API key validation"""
    print("🔑 Testing API Key Validation...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False
    
    provider = OpenAIProvider(api_key=api_key)
    
    try:
        is_valid = await provider.validate_api_key(api_key)
        print(f"✅ API key is valid: {is_valid}")
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


async def test_chat():
    """Test non-streaming chat completion"""
    print("\n💬 Testing Chat Completion...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False
    
    provider = OpenAIProvider(api_key=api_key)
    
    try:
        messages = [{"role": "user", "content": "Say hello in exactly 3 words"}]
        
        result_generator = provider.chat_completion(messages, stream=False)
        results = []
        async for chunk in result_generator:
            results.append(chunk)
        
        print(f"✅ Response: {results[0]}")
        return True
    except Exception as e:
        print(f"❌ Chat failed: {e}")
        return False


async def test_streaming():
    """Test streaming chat completion"""
    print("\n⚡ Testing Streaming Chat...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False
    
    provider = OpenAIProvider(api_key=api_key)
    
    try:
        messages = [{"role": "user", "content": "Count from 1 to 5, one number per word"}]
        
        print("✅ Streaming response: ", end="")
        result_generator = provider.chat_completion(messages, stream=True)
        async for chunk in result_generator:
            print(chunk, end="", flush=True)
        print()  # New line after streaming
        return True
    except Exception as e:
        print(f"❌ Streaming failed: {e}")
        return False


async def test_embeddings():
    """Test embedding creation"""
    print("\n🔢 Testing Embeddings...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False
    
    provider = OpenAIProvider(api_key=api_key)
    try:
        texts = ["Hello world", "This is a test", "AI embeddings are cool"]
        embeddings = await provider.create_embeddings(texts)
        
        print(f"✅ Created embeddings for {len(texts)} texts")
        print(f"   Embedding dimensions: {len(embeddings[0])}")
        print(f"   First few values: {embeddings[0][:5]}")
        return True
    except Exception as e:
        print(f"❌ Embeddings failed: {e}")
        return False


async def test_image():
    """Test image analysis"""
    print("\n🖼️  Testing Image Analysis...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False
    
    provider = OpenAIProvider(api_key=api_key)
    
    try:
        # Create a simple 1x1 red pixel PNG for testing
        test_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xd2\x00\x00\x00\x00\x00\x05\x17v\x06\xf9\x00\x00\x00\x00IEND\xaeB`\x82'
        
        analysis = await provider.analyze_image(test_image, "What color is this image?")
        print(f"✅ Image analysis: {analysis[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Image analysis failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("🚀 Running All AI Provider Tests\n")
    
    tests = [
        ("Validation", test_validation),
        ("Chat", test_chat),
        ("Streaming", test_streaming),
        ("Embeddings", test_embeddings),
        ("Image Analysis", test_image)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    print(f"\n📊 Test Results:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check your API key and network connection")


def show_usage():
    """Show usage information"""
    print(__doc__)


async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "validate":
        await test_validation()
    elif command == "chat":
        await test_chat()
    elif command == "stream":
        await test_streaming()
    elif command == "embed":
        await test_embeddings()
    elif command == "image":
        await test_image()
    elif command == "all":
        await run_all_tests()
    elif command in ["help", "-h", "--help"]:
        show_usage()
    else:
        print(f"❌ Unknown command: {command}")
        show_usage()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)
