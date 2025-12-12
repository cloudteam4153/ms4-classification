"""Database connection and session management"""

from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import uuid

from utils.config import config

# Create SQLAlchemy Base
Base = declarative_base()

# Database engine and session
engine = None
SessionLocal = None

def get_uuid_column():
    """Get appropriate UUID column type based on database"""
    if config.DB_TYPE == "postgresql":
        return PostgreSQL_UUID(as_uuid=True)
    else:  # MySQL
        return CHAR(36)

# SQLAlchemy Models
class ClassificationDB(Base):
    """Classification database model"""
    __tablename__ = "classifications"
    
    cls_id = Column(get_uuid_column(), primary_key=True, default=uuid.uuid4)
    msg_id = Column(get_uuid_column(), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # Added for user filtering
    label = Column(SQLEnum('todo', 'followup', 'noise', name='classification_label'), nullable=False)
    priority = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Classification(cls_id={self.cls_id}, msg_id={self.msg_id}, user_id={self.user_id}, label={self.label})>"


def init_database():
    """Initialize database connection"""
    global engine, SessionLocal
    
    try:
        # Get database URL
        database_url = config.get_database_url()
        
        # Create engine
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=not config.is_production()  # Log SQL in development
        )
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Run migrations (add user_id column if it doesn't exist)
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                # Check if user_id column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='classifications' AND column_name='user_id';
                """))
                
                if not result.fetchone():
                    print("🔄 Running migration: Adding user_id column...")
                    conn.execute(text("ALTER TABLE classifications ADD COLUMN user_id VARCHAR(255);"))
                    conn.execute(text("CREATE INDEX idx_classifications_user_id ON classifications(user_id);"))
                    conn.commit()
                    print("✅ Migration complete: user_id column added")
        except Exception as e:
            print(f"⚠️  Migration warning: {e}")
        
        print(f"✅ Database connected successfully: {config.DB_TYPE}://{config.DB_HOST}/{config.DB_NAME}")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Using in-memory storage as fallback")
        return False


def get_db() -> Generator[Session, None, None]:
    """
    Get database session (for FastAPI dependency injection)
    
    Usage:
        @app.get("/classifications")
        def list_classifications(db: Session = Depends(get_db)):
            return db.query(ClassificationDB).all()
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session as context manager
    
    Usage:
        with get_db_session() as db:
            classification = db.query(ClassificationDB).first()
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_database_connection() -> bool:
    """Test if database connection is working"""
    try:
        with get_db_session() as db:
            # Try a simple query
            db.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False


# Cloud SQL Connector (for production)
def init_cloud_sql_connection():
    """Initialize Cloud SQL connection using Cloud SQL Python Connector"""
    global engine, SessionLocal
    
    if not config.USE_CLOUD_SQL_CONNECTOR or not config.CLOUD_SQL_CONNECTION_NAME:
        return False
    
    try:
        from google.cloud.sql.connector import Connector
        
        # Initialize connector
        connector = Connector()
        
        def getconn():
            return connector.connect(
                config.CLOUD_SQL_CONNECTION_NAME,
                "pg8000" if config.DB_TYPE == "postgresql" else "pymysql",
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                db=config.DB_NAME,
            )
        
        # Create engine with Cloud SQL connector
        if config.DB_TYPE == "postgresql":
            engine = create_engine(
                "postgresql+pg8000://",
                creator=getconn,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
        else:
            engine = create_engine(
                "mysql+pymysql://",
                creator=getconn,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        
        print(f"✅ Cloud SQL connected: {config.CLOUD_SQL_CONNECTION_NAME}")
        return True
        
    except Exception as e:
        print(f"❌ Cloud SQL connection failed: {e}")
        return False

