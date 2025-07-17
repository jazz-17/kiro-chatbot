# AI Provider Testing Guide

## Quick Setup

### 1. Set up your OpenAI API Key

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and replace `your-openai-api-key-here` with your actual OpenAI API key:
   ```bash
   nano .env
   ```
   
   Or use any text editor to edit the `.env` file and update this line:
   ```
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   ```

### 2. Test the AI Provider

#### Option 1: Simple CLI Tests (Recommended)
```bash
# Test all functionality
python test_cli.py all

# Test individual features
python test_cli.py validate    # Test API key
python test_cli.py chat        # Test chat completion
python test_cli.py stream      # Test streaming
python test_cli.py embed       # Test embeddings
python test_cli.py image       # Test image analysis
```

#### Option 2: Comprehensive Manual Tests
```bash
python test_manual_providers.py
```

#### Option 3: Unit Tests (No API key needed)
```bash
pytest test_ai_providers.py -v
```

## Example Output

When working correctly, you should see output like:

```
🚀 Running All AI Provider Tests

🔑 Testing API Key Validation...
✅ API key is valid: True

💬 Testing Chat Completion...
✅ Response: Hello there, friend!

⚡ Testing Streaming Chat...
✅ Streaming response: One Two Three Four Five

🔢 Testing Embeddings...
✅ Created embeddings for 3 texts
   Embedding dimensions: 1536
   First few values: [0.123, -0.456, 0.789, 0.012, -0.345]

🖼️  Testing Image Analysis...
✅ Image analysis: This appears to be a simple red colored image or pixel...

📊 Test Results:
   Validation: ✅ PASS
   Chat: ✅ PASS
   Streaming: ✅ PASS
   Embeddings: ✅ PASS
   Image Analysis: ✅ PASS

Summary: 5/5 tests passed
🎉 All tests passed!
```

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not found"**
   - Make sure you created the `.env` file
   - Check that your API key is properly set in the `.env` file
   - Ensure your API key starts with `sk-`

2. **"Invalid API key"**
   - Verify your OpenAI API key is correct
   - Check if your API key has sufficient credits
   - Make sure you're using the correct format

3. **"Rate limit exceeded"**
   - You've hit OpenAI's rate limits
   - Wait a few minutes and try again
   - Consider upgrading your OpenAI plan

4. **Import errors**
   - Make sure you're in the `/api` directory
   - Run `uv sync` to install dependencies

### Getting an OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)
6. Add credits to your account for usage

## Environment Variables

The `.env` file supports these variables:

```bash
# Required
OPENAI_API_KEY=sk-your-api-key-here

# Optional
OPENAI_BASE_URL=https://api.openai.com/v1  # For custom endpoints
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
DEBUG=true
LOG_LEVEL=INFO
```
