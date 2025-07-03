# Test Configuration
# This file is loaded when tests are run to set up the test environment

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

# Use SQLite for testing if no DATABASE_URL is set
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

print("✅ Test environment configured")
