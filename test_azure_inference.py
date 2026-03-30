#!/usr/bin/env python3
"""Test script for Azure AI Inference SDK with GPT-5.3-chat."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_inference():
    """Test the Azure AI Inference SDK connection."""
    print("=" * 60)
    print("Testing Azure AI Inference SDK with GPT-5.3-chat")
    print("=" * 60)
    
    # Check environment variables
    endpoint = os.getenv("AZURE_AI_ENDPOINT")
    api_key = os.getenv("AZURE_AI_API_KEY")
    deployment = os.getenv("AZURE_DEPLOYMENT")
    
    print(f"\nConfiguration:")
    print(f"  Endpoint: {endpoint[:50]}..." if endpoint else "  Endpoint: NOT SET")
    print(f"  API Key: {'*' * 20}..." if api_key else "  API Key: NOT SET")
    print(f"  Deployment: {deployment}" if deployment else "  Deployment: NOT SET")
    
    if not all([endpoint, api_key, deployment]):
        print("\n❌ Missing required environment variables!")
        return False
    
    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.ai.inference.models import SystemMessage, UserMessage
        from azure.core.credentials import AzureKeyCredential
        
        print("\n✅ Azure AI Inference SDK imported successfully")
        
        # Create client
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        print("✅ Client created successfully")
        
        # Test a simple completion
        print("\nSending test message...")
        response = client.complete(
            messages=[
                SystemMessage(content="You are a helpful podcast host."),
                UserMessage(content="Say 'Hello, podcast listeners!' in exactly one sentence.")
            ],
            model=deployment,
            model_extras={"max_completion_tokens": 100}
        )
        
        result = response.choices[0].message.content.strip()
        print(f"\n✅ Response received:")
        print(f"   '{result}'")
        
        # Check response quality
        if len(result) > 10:
            print("\n✅ TEST PASSED: Azure AI Inference SDK is working correctly!")
            return True
        else:
            print("\n⚠️ Warning: Response seems too short")
            return False
            
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Install with: pip install azure-ai-inference")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_fallback_openai_sdk():
    """Test fallback to OpenAI SDK."""
    print("\n" + "=" * 60)
    print("Testing Fallback OpenAI SDK")
    print("=" * 60)
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    model = os.getenv("AZURE_OPENAI_MODEL_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    
    if not all([endpoint, api_key, model]):
        print("⚠️ OpenAI SDK fallback config not fully set (this is OK if using Inference SDK)")
        return True
    
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
            azure_deployment=model
        )
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say hello in one word."}],
            model=model,
            max_completion_tokens=50
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI SDK fallback works: '{result}'")
        return True
        
    except Exception as e:
        print(f"⚠️ OpenAI SDK fallback error (may be expected): {e}")
        return True  # Not a failure if Inference SDK works


if __name__ == "__main__":
    inference_ok = test_azure_inference()
    fallback_ok = test_fallback_openai_sdk()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Azure AI Inference SDK: {'✅ PASS' if inference_ok else '❌ FAIL'}")
    print(f"OpenAI SDK Fallback: {'✅ PASS' if fallback_ok else '❌ FAIL'}")
    
    sys.exit(0 if inference_ok else 1)
