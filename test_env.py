import os
from dotenv import load_dotenv

print("Loading .env file...")
load_dotenv()

db_url = os.getenv("DATABASE_URL")
if db_url:
    print("✅ DATABASE_URL found")
    print(f"📋 URL starts with: {db_url[:30]}...")
    print(f"📋 Contains postgres user: {'postgres.hyveecaauycxceafzabi' in db_url}")
    print(f"📋 Contains asyncpg: {'+asyncpg' in db_url}")
else:
    print("❌ DATABASE_URL not found!")

# List all environment variables that start with DATABASE
for key, value in os.environ.items():
    if key.startswith('DATABASE'):
        print(f"Found env var: {key} = {value[:30]}...")
