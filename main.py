from __future__ import annotations

import os
import socket
from datetime import datetime, date
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query, Path, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from models.health import Health
from models.message import MessageRead, MessageCreate
from models.classification import (
    ClassificationRead, ClassificationCreate, ClassificationUpdate,
    ClassificationRequest, ClassificationResponse
)
from models.brief import BriefRead, BriefCreate, BriefRequest, BriefItem
from models.task import TaskRead, TaskCreate, TaskUpdate, TaskGenerationRequest, TaskGenerationResponse
from services.ai_classifier import AIClassifier
from services.task_generator import TaskGenerator
from services.integrations_client import integrations_client
from middleware.auth import get_current_user, get_optional_user, extract_user_id
from utils.config import config
from utils.database import init_database, init_cloud_sql_connection, get_db, ClassificationDB
from utils.pubsub_client import pubsub_client

port = config.FASTAPIPORT

# -----------------------------------------------------------------------------
# Fallback in-memory storage (if database fails)
# -----------------------------------------------------------------------------
classifications_memory: Dict[UUID, ClassificationRead] = {}
briefs: Dict[UUID, BriefRead] = {}
tasks: Dict[UUID, TaskRead] = {}
use_database = False

# Initialize services
ai_classifier = AIClassifier()
task_generator = TaskGenerator()

app = FastAPI(
    title="Classification Microservice API",
    description="AI-powered message classification service with OpenAI integration",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global use_database
    
    print("🚀 Starting Classification Microservice...")
    print(f"   Environment: {config.ENVIRONMENT}")
    print(f"   Port: {config.FASTAPIPORT}")
    
    # Validate configuration
    try:
        config.validate()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"⚠️  Configuration warning: {e}")
    
    # Initialize database
    if config.USE_CLOUD_SQL_CONNECTOR:
        use_database = init_cloud_sql_connection()
    else:
        use_database = init_database()
    
    if not use_database:
        print("⚠️  Running in fallback mode with in-memory storage")
    
    print("✅ Service started successfully")

# -----------------------------------------------------------------------------
# Health endpoints
# -----------------------------------------------------------------------------

def make_health(echo: Optional[str], path_echo: Optional[str] = None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo
    )

@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    return make_health(echo=echo, path_echo=None)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)

# -----------------------------------------------------------------------------
# Message endpoints (proxy to integrations service)
# -----------------------------------------------------------------------------

@app.get("/messages", response_model=List[MessageRead])
async def list_messages(
    channel: Optional[str] = Query(None, description="Filter by channel (gmail/slack)"),
    limit: Optional[int] = Query(50, description="Maximum number of messages to return"),
    user: Optional[dict] = Depends(get_optional_user)
):
    """
    List messages from integrations service
    
    NOTE: This is a proxy endpoint. In production, the frontend should call
    Sanjay's integrations service directly for messages. This is here for
    testing and compatibility.
    """
    try:
        # Get token if user is authenticated
        token = None
        # Note: In production, you'd pass the actual JWT token here
        
        messages = await integrations_client.get_messages(
            token=token,
            limit=limit,
            channel=channel
        )
        return messages
    except Exception as e:
        print(f"Error fetching messages: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch messages from integrations service"
        )

@app.get("/messages/{message_id}", response_model=MessageRead)
async def get_message(
    message_id: UUID,
    user: Optional[dict] = Depends(get_optional_user)
):
    """Get a specific message by ID from integrations service"""
    try:
        message = await integrations_client.get_message_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return message
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching message: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch message from integrations service"
        )

# -----------------------------------------------------------------------------
# Classification endpoints
# -----------------------------------------------------------------------------

def get_db_optional():
    """Get database session or None if database is not available"""
    if use_database:
        return next(get_db())
    return None

@app.post("/classifications", response_model=ClassificationResponse, status_code=201)
async def classify_messages(
    request: ClassificationRequest,
    user: Optional[dict] = Depends(get_optional_user),  # Optional JWT authentication
):
    """
    Classify new messages for a user using AI (OpenAI)
    
    Requires user_id. Only classifies messages that haven't been classified yet.
    This ensures one classification per message_id per user.
    
    JWT tokens are optional (handled by composite service)
    """
    # Require user_id
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    user_id_for_storage = request.user_id
    
    # Fetch all messages from integrations service
    all_messages = await integrations_client.get_messages(limit=100)
    
    if not all_messages:
        raise HTTPException(status_code=404, detail="No messages found")
    
    # Get already-classified message_ids for this user
    already_classified_msg_ids = set()
    if use_database:
        from utils.database import get_db_session
        with get_db_session() as db:
            existing = db.query(ClassificationDB.msg_id).filter(
                ClassificationDB.user_id == user_id_for_storage
            ).all()
            already_classified_msg_ids = {str(row[0]) for row in existing}
    else:
        # Fallback: check in-memory storage
        for cls in classifications_memory.values():
            if hasattr(cls, 'user_id') and cls.user_id == user_id_for_storage:
                already_classified_msg_ids.add(str(cls.msg_id))
    
    # Filter to only NEW messages (not yet classified)
    messages_to_classify = [
        msg for msg in all_messages 
        if str(msg.msg_id) not in already_classified_msg_ids
    ]
    
    if not messages_to_classify:
        # All messages already classified
        return ClassificationResponse(
            classifications=[],
            total_processed=0,
            success_count=0,
            error_count=0
        )
    
    # Classify messages using AI
    response = ai_classifier.classify_messages(messages_to_classify)
    
    # Update classifications with user_id
    updated_classifications = []
    for classification in response.classifications:
        # Create new classification with user_id
        updated_cls = ClassificationRead(
            cls_id=classification.cls_id,
            msg_id=classification.msg_id,
            user_id=user_id_for_storage,
            label=classification.label,
            priority=classification.priority,
            created_at=classification.created_at
        )
        updated_classifications.append(updated_cls)
    
    # Store classifications in database
    if use_database:
        from utils.database import get_db_session
        with get_db_session() as db:
            for classification in updated_classifications:
                db_classification = ClassificationDB(
                    cls_id=classification.cls_id,
                    msg_id=classification.msg_id,
                    user_id=user_id_for_storage,
                    label=classification.label.value,
                    priority=classification.priority,
                    created_at=classification.created_at
                )
                db.add(db_classification)
            db.commit()
    else:
        # Fallback to in-memory storage
        for classification in updated_classifications:
            classifications_memory[classification.cls_id] = classification
    
    # Emit events to Pub/Sub for each classification
    # This triggers the Google Cloud Function (requirement fulfilled!)
    for classification in updated_classifications:
        pubsub_client.publish_classification_event({
            "cls_id": classification.cls_id,
            "msg_id": classification.msg_id,
            "label": classification.label.value,
            "priority": classification.priority,
            "created_at": classification.created_at
        })
    
    # Return response with updated classifications
    return ClassificationResponse(
        classifications=updated_classifications,
        total_processed=response.total_processed,
        success_count=response.success_count,
        error_count=response.error_count
    )

@app.get("/classifications", response_model=List[ClassificationRead])
def list_classifications(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    label: Optional[str] = Query(None, description="Filter by classification label"),
    min_priority: Optional[int] = Query(None, description="Minimum priority score"),
    max_priority: Optional[int] = Query(None, description="Maximum priority score"),
    limit: Optional[int] = Query(100, description="Maximum number of results"),
    user: Optional[dict] = Depends(get_optional_user)
):
    """List classifications with optional filtering (supports user_id for composite)"""
    
    if use_database:
        from utils.database import get_db_session
        with get_db_session() as db:
            # Query from database
            query = db.query(ClassificationDB)
            
            if user_id:
                query = query.filter(ClassificationDB.user_id == user_id)
            if label:
                query = query.filter(ClassificationDB.label == label)
            if min_priority is not None:
                query = query.filter(ClassificationDB.priority >= min_priority)
            if max_priority is not None:
                query = query.filter(ClassificationDB.priority <= max_priority)
            
            query = query.order_by(ClassificationDB.created_at.desc()).limit(limit)
            db_results = query.all()
            
            # Convert to Pydantic models
            results = []
            for db_cls in db_results:
                results.append(ClassificationRead(
                    cls_id=db_cls.cls_id,
                    msg_id=db_cls.msg_id,
                    user_id=db_cls.user_id,
                    label=db_cls.label,
                    priority=db_cls.priority,
                    created_at=db_cls.created_at
                ))
            return results
    else:
        # Fallback to in-memory storage
        results = list(classifications_memory.values())
        
        if label:
            results = [c for c in results if c.label.value == label]
        if min_priority is not None:
            results = [c for c in results if c.priority >= min_priority]
        if max_priority is not None:
            results = [c for c in results if c.priority <= max_priority]
        
        return results[:limit]

@app.get("/classifications/{classification_id}", response_model=ClassificationRead)
def get_classification(
    classification_id: UUID,
    user: Optional[dict] = Depends(get_optional_user)
):
    """Get a specific classification by ID"""
    
    if use_database:
        from utils.database import get_db_session
        with get_db_session() as db:
            db_cls = db.query(ClassificationDB).filter(ClassificationDB.cls_id == classification_id).first()
            if not db_cls:
                raise HTTPException(status_code=404, detail="Classification not found")
            
            return ClassificationRead(
                cls_id=db_cls.cls_id,
                msg_id=db_cls.msg_id,
                user_id=db_cls.user_id,
                label=db_cls.label,
                priority=db_cls.priority,
                created_at=db_cls.created_at
            )
    else:
        if classification_id not in classifications_memory:
            raise HTTPException(status_code=404, detail="Classification not found")
        return classifications_memory[classification_id]

@app.put("/classifications/{classification_id}", response_model=ClassificationRead)
def update_classification(
    classification_id: UUID,
    update: ClassificationUpdate,
    user: Optional[dict] = Depends(get_optional_user)  # Optional JWT authentication
):
    """Update a classification (requires authentication)"""
    
    if use_database:
        from utils.database import get_db_session
        with get_db_session() as db:
            db_cls = db.query(ClassificationDB).filter(ClassificationDB.cls_id == classification_id).first()
            if not db_cls:
                raise HTTPException(status_code=404, detail="Classification not found")
            
            # Update fields
            if update.label is not None:
                db_cls.label = update.label.value
            if update.priority is not None:
                db_cls.priority = update.priority
            
            db.commit()
            db.refresh(db_cls)
            
            return ClassificationRead(
                cls_id=db_cls.cls_id,
                msg_id=db_cls.msg_id,
                user_id=db_cls.user_id,
                label=db_cls.label,
                priority=db_cls.priority,
                created_at=db_cls.created_at
            )
    else:
        if classification_id not in classifications_memory:
            raise HTTPException(status_code=404, detail="Classification not found")
        
        stored = classifications_memory[classification_id].model_dump()
        stored.update(update.model_dump(exclude_unset=True))
        
        classifications_memory[classification_id] = ClassificationRead(**stored)
        return classifications_memory[classification_id]

@app.delete("/classifications/{classification_id}")
def delete_classification(
    classification_id: UUID,
    user: Optional[dict] = Depends(get_optional_user)  # Optional JWT authentication
):
    """Delete a classification (requires authentication)"""
    
    if use_database:
        from utils.database import get_db_session
        with get_db_session() as db:
            db_cls = db.query(ClassificationDB).filter(ClassificationDB.cls_id == classification_id).first()
            if not db_cls:
                raise HTTPException(status_code=404, detail="Classification not found")
            
            db.delete(db_cls)
            db.commit()
    else:
        if classification_id not in classifications_memory:
            raise HTTPException(status_code=404, detail="Classification not found")
        del classifications_memory[classification_id]
    
    return {"message": "Classification deleted successfully"}

@app.delete("/admin/reset-database")
def reset_database(confirm: str = Query(..., description="Must be 'DELETE_ALL' to confirm")):
    """
    ADMIN ONLY: Delete all classifications from database
    
    WARNING: This deletes ALL data! Use with caution.
    Must pass ?confirm=DELETE_ALL
    """
    if confirm != "DELETE_ALL":
        raise HTTPException(status_code=400, detail="Must confirm with ?confirm=DELETE_ALL")
    
    if use_database:
        from utils.database import get_db_session
        from sqlalchemy import text
        with get_db_session() as db:
            result = db.execute(text("DELETE FROM classifications"))
            db.commit()
            deleted_count = result.rowcount
    else:
        deleted_count = len(classifications_memory)
        classifications_memory.clear()
    
    return {
        "message": "Database reset complete",
        "deleted_count": deleted_count
    }

@app.delete("/admin/delete-user-classifications")
def delete_user_classifications(
    user_id: str = Query(..., description="User ID to delete classifications for"),
    confirm: str = Query(..., description="Must be 'DELETE' to confirm")
):
    """
    ADMIN ONLY: Delete all classifications for a specific user
    
    Usage: /admin/delete-user-classifications?user_id=test_user&confirm=DELETE
    """
    if confirm != "DELETE":
        raise HTTPException(status_code=400, detail="Must confirm with ?confirm=DELETE")
    
    if use_database:
        from utils.database import get_db_session
        from sqlalchemy import text
        with get_db_session() as db:
            result = db.execute(
                text("DELETE FROM classifications WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            db.commit()
            deleted_count = result.rowcount
    else:
        # Fallback to in-memory storage
        to_delete = [
            cls_id for cls_id, cls in classifications_memory.items()
            if hasattr(cls, 'user_id') and cls.user_id == user_id
        ]
        for cls_id in to_delete:
            del classifications_memory[cls_id]
        deleted_count = len(to_delete)
    
    return {
        "message": f"Deleted classifications for user: {user_id}",
        "user_id": user_id,
        "deleted_count": deleted_count
    }

# -----------------------------------------------------------------------------
# Brief endpoints
# -----------------------------------------------------------------------------

@app.post("/briefs", response_model=BriefRead, status_code=201)
async def create_brief(request: BriefRequest):
    """Generate a daily brief for a user"""
    if request.date:
        try:
            brief_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        brief_date = date.today()
    max_items = request.max_items or 50
    
    # Get classifications for the user (in a real system, this would filter by user_id)
    user_classifications = list(classifications_memory.values())
    
    # Filter by date and sort by priority
    # For now, include all classifications since we're using in-memory storage
    today_classifications = user_classifications
    
    # Sort by priority score (highest first)
    today_classifications.sort(key=lambda x: x.priority, reverse=True)
    
    # Take top items
    top_classifications = today_classifications[:max_items]
    
    # Fetch messages from integrations service
    all_messages = await integrations_client.get_messages(limit=100)
    messages_dict = {msg.msg_id: msg for msg in all_messages}
    
    # Create brief items
    brief_items = []
    for classification in top_classifications:
        if classification.msg_id in messages_dict:
            message = messages_dict[classification.msg_id]
            brief_item = BriefItem(
                classification_id=classification.cls_id,
                message_id=classification.msg_id,
                title=f"{classification.label.value.title()}: {message.subject or 'No Subject'}",
                description=message.snippet[:200] + "..." if len(message.snippet) > 200 else message.snippet,
                priority_score=classification.priority,
                channel=message.channel.value,
                sender=message.sender,
                received_at=message.received_at,
                extracted_tasks=[]
            )
            brief_items.append(brief_item)
    
    # Count items by type
    todo_count = len([c for c in top_classifications if c.label.value == "todo"])
    followup_count = len([c for c in top_classifications if c.label.value == "followup"])
    high_priority_count = len([c for c in top_classifications if c.priority >= 7])
    
    # Create brief
    brief = BriefRead(
        brief_id=uuid4(),
        user_id=request.user_id,
        brief_date=brief_date,
        total_items=len(brief_items),
        high_priority_count=high_priority_count,
        todo_count=todo_count,
        followup_count=followup_count,
        items=brief_items,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    briefs[brief.brief_id] = brief
    return brief

@app.get("/briefs", response_model=List[BriefRead])
def list_briefs(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    brief_date: Optional[date] = Query(None, description="Filter by brief date")
):
    """List briefs with optional filtering"""
    results = list(briefs.values())
    
    if user_id:
        results = [b for b in results if b.user_id == user_id]
    if brief_date:
        results = [b for b in results if b.brief_date == brief_date]
    
    return results

@app.get("/briefs/{brief_id}", response_model=BriefRead)
def get_brief(brief_id: UUID):
    """Get a specific brief by ID"""
    if brief_id not in briefs:
        raise HTTPException(status_code=404, detail="Brief not found")
    return briefs[brief_id]

@app.delete("/briefs/{brief_id}")
def delete_brief(brief_id: UUID):
    """Delete a brief"""
    if brief_id not in briefs:
        raise HTTPException(status_code=404, detail="Brief not found")
    del briefs[brief_id]
    return {"message": "Brief deleted successfully"}

# -----------------------------------------------------------------------------
# Task endpoints
# -----------------------------------------------------------------------------

@app.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(task: TaskCreate):
    """Create a new task"""
    task_read = TaskRead(
        task_id=uuid4(),
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        source_message_id=task.source_message_id,
        created_at=datetime.utcnow()
    )
    tasks[task_read.task_id] = task_read
    return task_read

@app.get("/tasks", response_model=List[TaskRead])
def list_tasks(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by task priority"),
    limit: Optional[int] = Query(50, description="Maximum number of tasks to return")
):
    """List tasks with optional filtering"""
    results = list(tasks.values())
    
    if user_id:
        results = [t for t in results if t.user_id == user_id]
    if status:
        results = [t for t in results if t.status.value == status]
    if priority:
        try:
            priority_int = int(priority)
            results = [t for t in results if t.priority == priority_int]
        except ValueError:
            pass  # Invalid priority value, ignore filter
    
    return results[:limit]

@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID):
    """Get a specific task by ID"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: UUID, update: TaskUpdate):
    """Update a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    stored = tasks[task_id].model_dump()
    stored.update(update.model_dump(exclude_unset=True))
    stored["updated_at"] = datetime.utcnow()
    
    tasks[task_id] = TaskRead(**stored)
    return tasks[task_id]

@app.delete("/tasks/{task_id}")
def delete_task(task_id: UUID):
    """Delete a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return {"message": "Task deleted successfully"}

@app.post("/tasks/generate", response_model=TaskGenerationResponse, status_code=201)
async def generate_tasks(request: TaskGenerationRequest):
    """Generate tasks from classifications"""
    # Get classifications to generate tasks from
    classifications_to_process = []
    for cls_id in request.classification_ids:
        if cls_id in classifications_memory:
            classifications_to_process.append(classifications_memory[cls_id])
        else:
            raise HTTPException(status_code=404, detail=f"Classification {cls_id} not found")
    
    # Get associated messages from integrations service
    message_ids = [cls.msg_id for cls in classifications_to_process]
    all_messages = await integrations_client.get_messages(limit=100)
    messages_dict = {msg.msg_id: msg for msg in all_messages}
    
    messages_to_process = []
    for msg_id in message_ids:
        if msg_id in messages_dict:
            messages_to_process.append(messages_dict[msg_id])
        else:
            raise HTTPException(status_code=404, detail=f"Message {msg_id} not found")
    
    # Generate tasks
    response = task_generator.generate_tasks_from_classifications(
        classifications_to_process, messages_to_process, request
    )
    
    # Store generated tasks
    for task in response.tasks:
        tasks[task.task_id] = task
    
    return response

# -----------------------------------------------------------------------------
# Root endpoint
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to the Classification Microservice API",
        "description": "AI-powered message classification using OpenAI",
        "version": "2.0.0",
        "status": "online",
        "environment": config.ENVIRONMENT,
        "database": "connected" if use_database else "in-memory fallback",
        "ai_mode": "OpenAI API" if not ai_classifier.mock_mode else "Mock (no API key)",
        "endpoints": {
            "health": "/health",
            "classifications": "/classifications (POST requires JWT)",
            "messages": "/messages (proxy to integrations service)",
            "docs": "/docs"
        },
        "integrations": {
            "integrations_service": config.INTEGRATIONS_SERVICE_URL,
            "composite_service": config.COMPOSITE_SERVICE_URL
        }
    }

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)