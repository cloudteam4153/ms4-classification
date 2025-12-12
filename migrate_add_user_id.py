#!/usr/bin/env python3
"""
Migration script to add user_id column to classifications table
Run this once after deploying the updated code
"""

import os
import sys
from sqlalchemy import create_engine, text

# Import config
sys.path.insert(0, os.path.dirname(__file__))
from utils.config import config

def migrate():
    """Add user_id column to classifications table"""
    print("🔄 Starting migration: Add user_id column to classifications table")
    
    try:
        # Get database URL
        database_url = config.get_database_url()
        print(f"📊 Connecting to database: {config.DB_TYPE}://{config.DB_HOST}/{config.DB_NAME}")
        
        # Create engine
        engine = create_engine(database_url, pool_pre_ping=True)
        
        # Add user_id column
        with engine.connect() as conn:
            print("🔧 Adding user_id column...")
            
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='classifications' AND column_name='user_id';
            """))
            
            if result.fetchone():
                print("✅ user_id column already exists. No migration needed.")
                return
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE classifications 
                ADD COLUMN user_id VARCHAR(255);
            """))
            
            # Add index for faster queries
            conn.execute(text("""
                CREATE INDEX idx_classifications_user_id ON classifications(user_id);
            """))
            
            conn.commit()
            
            print("✅ Migration complete!")
            print("   - Added user_id column (VARCHAR(255))")
            print("   - Created index on user_id")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()

