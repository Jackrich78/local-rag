#!/usr/bin/env python3.10
"""
Test Graphiti setup and initialization with Neo4j.
"""
import os
import asyncio
from dotenv import load_dotenv
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient

# Load environment variables
load_dotenv()

async def test_graphiti_setup():
    """Test Graphiti initialization with Neo4j."""
    try:
        print("🔧 Testing Graphiti setup...")
        
        # Get configuration from .env
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER") 
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        openai_api_key = os.getenv("LLM_API_KEY")  # This should be the OpenAI key
        
        print(f"Neo4j URI: {neo4j_uri}")
        print(f"Neo4j User: {neo4j_user}")
        print(f"OpenAI API Key: {'Set' if openai_api_key and openai_api_key != 'your-openai-api-key-here' else 'Not Set'}")
        
        if not openai_api_key or openai_api_key == "your-openai-api-key-here":
            print("❌ OpenAI API key not set. Please update .env file with your API key.")
            return False
            
        # Configure LLM for Graphiti
        llm_config = LLMConfig(
            model="gpt-4o-mini",
            api_key=openai_api_key,
            base_url="https://api.openai.com/v1"
        )
        
        # Create Graphiti client
        print("📊 Creating Graphiti client...")
        graphiti = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password
        )
        
        # Test basic functionality
        print("🧪 Testing Graphiti basic operations...")
        
        # This should initialize the schema if needed
        await graphiti.add_episode(
            "This is a test message to initialize Graphiti schema in Neo4j."
        )
        
        print("✅ Graphiti setup successful!")
        print("   - Neo4j connection working")
        print("   - Schema initialized")
        print("   - OpenAI integration working")
        
        return True
        
    except Exception as e:
        print(f"❌ Graphiti setup failed: {e}")
        print("   This might be due to:")
        print("   - Missing OpenAI API key")
        print("   - Neo4j connection issues")
        print("   - Graphiti version compatibility")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_graphiti_setup())
    if success:
        print("\n🎉 Graphiti is ready for knowledge graph operations!")
    else:
        print("\n⚠️  Graphiti setup needs attention before proceeding.")