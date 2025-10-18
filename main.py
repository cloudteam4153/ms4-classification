from __future__ import annotations

import os
import socket
from datetime import datetime, date
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

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

port = int(os.environ.get("FASTAPIPORT", 8001))

# -----------------------------------------------------------------------------
# In-memory "databases" for the prioritizer service
# -----------------------------------------------------------------------------
messages: Dict[UUID, MessageRead] = {}
classifications: Dict[UUID, ClassificationRead] = {}
briefs: Dict[UUID, BriefRead] = {}
tasks: Dict[UUID, TaskRead] = {}

# Initialize services
ai_classifier = AIClassifier()
task_generator = TaskGenerator()

app = FastAPI(
    title="Prioritizer Service API",
    description="AI-powered message classification and prioritization service for unified inbox assistant",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Initialize sample data on startup"""
    initialize_sample_data()

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
# Message endpoints (for testing and integration)
# -----------------------------------------------------------------------------

@app.post("/messages", response_model=MessageRead, status_code=201)
def create_message(message: MessageCreate):
    """Create a new message (for testing purposes)"""
    message_read = MessageRead(
        msg_id=uuid4(),
        account_id=message.account_id,
        external_id=message.external_id,
        channel=message.channel,
        sender=message.sender,
        subject=message.subject,
        snippet=message.snippet,
        received_at=message.received_at,
        raw_ref=message.raw_ref,
        priority=message.priority,
        created_at=datetime.utcnow()
    )
    messages[message_read.msg_id] = message_read
    return message_read

@app.get("/messages", response_model=List[MessageRead])
def list_messages(
    channel: Optional[str] = Query(None, description="Filter by channel (gmail/slack)"),
    sender: Optional[str] = Query(None, description="Filter by sender"),
    limit: Optional[int] = Query(50, description="Maximum number of messages to return")
):
    """List messages with optional filtering"""
    results = list(messages.values())
    
    if channel:
        results = [m for m in results if m.channel.value == channel]
    if sender:
        results = [m for m in results if sender.lower() in m.sender.lower()]
    
    return results[:limit]

@app.get("/messages/{message_id}", response_model=MessageRead)
def get_message(message_id: UUID):
    """Get a specific message by ID"""
    if message_id not in messages:
        raise HTTPException(status_code=404, detail="Message not found")
    return messages[message_id]

# -----------------------------------------------------------------------------
# Classification endpoints
# -----------------------------------------------------------------------------

@app.post("/classifications", response_model=ClassificationResponse, status_code=201)
def classify_messages(request: ClassificationRequest):
    """Classify multiple messages using AI"""
    # Get messages to classify
    messages_to_classify = []
    for msg_id in request.message_ids:
        if msg_id in messages:
            messages_to_classify.append(messages[msg_id])
        else:
            raise HTTPException(status_code=404, detail=f"Message {msg_id} not found")
    
    # Classify messages using AI
    response = ai_classifier.classify_messages(messages_to_classify)
    
    # Store classifications
    for classification in response.classifications:
        classifications[classification.cls_id] = classification
    
    return response

@app.get("/classifications", response_model=List[ClassificationRead])
def list_classifications(
    label: Optional[str] = Query(None, description="Filter by classification label"),
    min_priority: Optional[int] = Query(None, description="Minimum priority score"),
    max_priority: Optional[int] = Query(None, description="Maximum priority score")
):
    """List classifications with optional filtering"""
    results = list(classifications.values())
    
    if label:
        results = [c for c in results if c.label.value == label]
    if min_priority is not None:
        results = [c for c in results if c.priority >= min_priority]
    if max_priority is not None:
        results = [c for c in results if c.priority <= max_priority]
    
    return results

@app.get("/classifications/{classification_id}", response_model=ClassificationRead)
def get_classification(classification_id: UUID):
    """Get a specific classification by ID"""
    if classification_id not in classifications:
        raise HTTPException(status_code=404, detail="Classification not found")
    return classifications[classification_id]

@app.put("/classifications/{classification_id}", response_model=ClassificationRead)
def update_classification(classification_id: UUID, update: ClassificationUpdate):
    """Update a classification"""
    if classification_id not in classifications:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    stored = classifications[classification_id].model_dump()
    stored.update(update.model_dump(exclude_unset=True))
    stored["updated_at"] = datetime.utcnow()
    
    classifications[classification_id] = ClassificationRead(**stored)
    return classifications[classification_id]

@app.delete("/classifications/{classification_id}")
def delete_classification(classification_id: UUID):
    """Delete a classification"""
    if classification_id not in classifications:
        raise HTTPException(status_code=404, detail="Classification not found")
    del classifications[classification_id]
    return {"message": "Classification deleted successfully"}

# -----------------------------------------------------------------------------
# Brief endpoints
# -----------------------------------------------------------------------------

@app.post("/briefs", response_model=BriefRead, status_code=201)
def create_brief(request: BriefRequest):
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
    user_classifications = list(classifications.values())
    
    # Filter by date and sort by priority
    # For now, include all classifications since we're using in-memory storage
    today_classifications = user_classifications
    
    # Sort by priority score (highest first)
    today_classifications.sort(key=lambda x: x.priority, reverse=True)
    
    # Take top items
    top_classifications = today_classifications[:max_items]
    
    # Create brief items
    brief_items = []
    for classification in top_classifications:
        if classification.msg_id in messages:
            message = messages[classification.msg_id]
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
def generate_tasks(request: TaskGenerationRequest):
    """Generate tasks from classifications"""
    # Get classifications to generate tasks from
    classifications_to_process = []
    for cls_id in request.classification_ids:
        if cls_id in classifications:
            classifications_to_process.append(classifications[cls_id])
        else:
            raise HTTPException(status_code=404, detail=f"Classification {cls_id} not found")
    
    # Get associated messages
    message_ids = [cls.msg_id for cls in classifications_to_process]
    messages_to_process = []
    for msg_id in message_ids:
        if msg_id in messages:
            messages_to_process.append(messages[msg_id])
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
        "message": "Welcome to the Prioritizer Service API",
        "description": "AI-powered message classification and task generation service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "classifications": "/classifications",
            "tasks": "/tasks",
            "briefs": "/briefs",
            "messages": "/messages (for testing)"
        },
        "docs": "/docs"
    }

# -----------------------------------------------------------------------------
# Initialize with sample data
# -----------------------------------------------------------------------------

def initialize_sample_data():
    """Initialize the service with sample data for testing"""
    
    # Create sample messages
    sample_messages = [
        MessageCreate(
            account_id=uuid4(),
            external_id="gmail_001",
            channel="gmail",
            sender="boss@company.com",
            subject="URGENT: Project Deadline Tomorrow",
            snippet="Hi team, I need the project status update by EOD tomorrow. This is critical for our client presentation.",
            received_at=datetime.utcnow(),
            raw_ref="gmail://thread/001"
        ),
        MessageCreate(
            account_id=uuid4(),
            external_id="slack_001",
            channel="slack",
            sender="john.doe@company.com",
            subject="Meeting Reminder",
            snippet="Don't forget about our team standup at 10 AM tomorrow. We'll discuss the sprint progress.",
            received_at=datetime.utcnow(),
            raw_ref="slack://channel/general/001"
        ),
        MessageCreate(
            account_id=uuid4(),
            external_id="gmail_002",
            channel="gmail",
            sender="newsletter@example.com",
            subject="Weekly Newsletter",
            snippet="Check out our latest updates and industry news. No action required.",
            received_at=datetime.utcnow(),
            raw_ref="gmail://thread/002"
        )
    ]
    
    # Create the messages
    for msg in sample_messages:
        create_message(msg)

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    # Initialize sample data
    initialize_sample_data()
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)