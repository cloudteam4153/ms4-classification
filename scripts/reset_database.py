#!/usr/bin/env python3
"""
Reset database - delete all classifications
WARNING: This will delete ALL data!
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.config import config
from sqlalchemy import create_engine, text

def reset_database():
    """Delete all classifications from database"""
    print("⚠️  WARNING: This will delete ALL classifications!")
    print(f"   Database: {config.DB_TYPE}://{config.DB_HOST}/{config.DB_NAME}")
    
    confirm = input("\nType 'DELETE ALL' to confirm: ")
    if confirm != "DELETE ALL":
        print("❌ Cancelled")
        return
    
    try:
        database_url = config.get_database_url()
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Delete all classifications
            result = conn.execute(text("DELETE FROM classifications"))
            conn.commit()
            
            print(f"\n✅ Deleted {result.rowcount} classifications")
            print("   Database is now empty")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_database()

