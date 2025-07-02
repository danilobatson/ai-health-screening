import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

async def test_connection():
    load_dotenv()
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    print(f"Testing connection to: {DATABASE_URL[:50]}...")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1 as test")
            value = result.scalar()
            print(f"✅ Connection successful! Test query returned: {value}")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_connection())
