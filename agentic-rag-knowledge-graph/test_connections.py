#!/usr/bin/env python3
"""
Test connectivity to PostgreSQL and Neo4j.
"""
import asyncio
import os
from dotenv import load_dotenv
import asyncpg
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

async def test_postgres_connection():
    """Test PostgreSQL connection via Supabase pooler."""
    try:
        database_url = os.getenv("DATABASE_URL")
        print(f"Testing PostgreSQL connection to: {database_url}")
        
        conn = await asyncpg.connect(database_url)
        
        # Test basic query
        result = await conn.fetchrow("SELECT 1 as test, version() as pg_version")
        print(f"✅ PostgreSQL connected successfully!")
        print(f"   Test query result: {result['test']}")
        print(f"   PostgreSQL version: {result['pg_version'][:50]}...")
        
        # Test our tables exist
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('documents', 'chunks', 'sessions', 'messages')
            ORDER BY table_name
        """)
        print(f"   Our tables: {[row['table_name'] for row in tables]}")
        
        # Test vector extension
        vector_check = await conn.fetchrow("SELECT vector('[1,2,3]') as test_vector")
        print(f"   Vector extension working: {vector_check['test_vector']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def test_neo4j_connection():
    """Test Neo4j connection."""
    try:
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        print(f"Testing Neo4j connection to: {neo4j_uri}")
        
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Test basic query
        with driver.session() as session:
            result = session.run("RETURN 1 as test, 'Neo4j connected!' as message")
            record = result.single()
            print(f"✅ Neo4j connected successfully!")
            print(f"   Test query result: {record['test']}")
            print(f"   Message: {record['message']}")
            
            # Check database info
            db_info = session.run("CALL dbms.components() YIELD name, versions")
            for record in db_info:
                print(f"   {record['name']}: {record['versions'][0]}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

async def main():
    """Run all connection tests."""
    print("🔌 Testing Database Connections...\n")
    
    print("=" * 50)
    postgres_ok = await test_postgres_connection()
    
    print("\n" + "=" * 50)
    neo4j_ok = test_neo4j_connection()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   PostgreSQL: {'✅ Connected' if postgres_ok else '❌ Failed'}")
    print(f"   Neo4j: {'✅ Connected' if neo4j_ok else '❌ Failed'}")
    
    if postgres_ok and neo4j_ok:
        print("\n🎉 All connections successful! Ready to proceed.")
        return True
    else:
        print("\n⚠️  Some connections failed. Check configuration.")
        return False

if __name__ == "__main__":
    asyncio.run(main())