import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection():
    load_dotenv()
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    print(f"Testing connection to Supabase...")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)  # Less verbose
        
        async with engine.begin() as conn:
            # Use text() for raw SQL in SQLAlchemy 2.0+
            result = await conn.execute(text("SELECT 1 as test, current_user as username"))
            row = result.fetchone()
            print(f"✅ Connection successful!")
            print(f"✅ Test query returned: {row[0]}")
            print(f"✅ Connected as user: {row[1]}")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if success:
        print("🎉 Database is ready for FastAPI!")
