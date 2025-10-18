# Prioritizer Service - AI-Powered Message Classification

A FastAPI-based microservice for AI-powered message classification and task generation as part of a unified inbox assistant. This service classifies Gmail and Slack messages into actionable tasks and generates daily briefs.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- pip (Python package manager)

### Installation & Running

1. **Clone and navigate to the project:**
```bash
git clone <your-repo-url>
cd ms4-classification
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start the service:**
```bash
python main.py
```

4. **Access the service:**
- **API Base URL:** `http://localhost:8001`
- **Interactive Documentation:** `http://localhost:8001/docs` (Swagger UI)
- **Alternative Docs:** `http://localhost:8001/redoc` (ReDoc)

## 📋 What This Service Does

This microservice is part of a **unified inbox assistant** that helps users manage their Gmail and Slack messages by:

1. **Classifying Messages**: Uses AI to categorize messages as `todo`, `followup`, or `noise`
2. **Assigning Priorities**: Gives each message a priority score from 1-10 based on content analysis
3. **Generating Tasks**: Creates actionable tasks from classified messages
4. **Creating Daily Briefs**: Summarizes high-priority items for users

## 🔧 Features

- **AI Classification**: Smart message analysis using AI prompts (currently mocked)
- **Priority Scoring**: Intelligent priority assignment (1-10 scale)
- **Task Generation**: Automatic task creation from classified messages
- **Daily Briefs**: Personalized summaries of important items
- **Health Monitoring**: Built-in health check endpoints
- **Interactive API Docs**: Auto-generated Swagger/OpenAPI documentation

## 📚 API Documentation

### View All Endpoints
Visit `http://localhost:8001/docs` to see the interactive API documentation where you can:
- View all available endpoints
- Test API calls directly in the browser
- See request/response schemas
- Download OpenAPI specification

### Key Endpoints

#### Health Check
- `GET /health` - Service health status

#### Message Classification
- `POST /classifications` - Classify messages using AI
- `GET /classifications` - List classifications with filtering

#### Task Management
- `POST /tasks/generate` - Generate tasks from classifications
- `GET /tasks` - List tasks with filtering
- `POST /tasks` - Create manual tasks
- `PUT /tasks/{task_id}` - Update tasks
- `DELETE /tasks/{task_id}` - Delete tasks

#### Daily Briefs
- `POST /briefs` - Generate daily brief for user
- `GET /briefs` - List briefs with filtering

#### Testing (Sample Data)
- `GET /messages` - View sample messages for testing

## 🗄️ Database Schema

The service uses a simplified schema that matches your team's MySQL database:

```sql
-- Core tables
users(user_id, email, created_at)
accounts(account_id, user_id, provider ENUM('gmail','slack'), access_token_hash, meta)
messages(msg_id, account_id, external_id, channel, sender, subject, snippet, received_at, raw_ref, priority)
classifications(cls_id, msg_id, label ENUM('todo','followup','noise'), priority, created_at)
tasks(task_id, user_id, source_msg_id, title, status ENUM('open','done'), due_at, priority, description, created_at)
```

## 🧪 Testing the Service

### 1. Check Service Health
```bash
curl http://localhost:8001/health
```

### 2. View Sample Data
```bash
curl http://localhost:8001/messages
```

### 3. Test Classification
```bash
# Get a message ID first
MESSAGE_ID=$(curl -s http://localhost:8001/messages | jq -r '.[0].msg_id')

# Classify the message
curl -X POST "http://localhost:8001/classifications" \
  -H "Content-Type: application/json" \
  -d "{\"message_ids\": [\"$MESSAGE_ID\"]}"
```

### 4. Generate Tasks
```bash
# Get a classification ID
CLASS_ID=$(curl -s http://localhost:8001/classifications | jq -r '.[0].cls_id')

# Generate tasks
curl -X POST "http://localhost:8001/tasks/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "classification_ids": ["'$CLASS_ID'"],
    "user_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

### 5. View Generated Tasks
```bash
curl http://localhost:8001/tasks
```

## 🔄 Service Workflow

1. **Ingestor Service** → Sends Gmail/Slack messages to this service
2. **This Service** → Classifies messages and generates tasks
3. **Actions Service** → Receives tasks for CRUD operations
4. **Desktop App** → Displays daily briefs and task management UI

## ⚙️ Configuration

### Port Configuration
Default port is 8001. Change it with:
```bash
export FASTAPIPORT=3001
python main.py
```

### Environment Variables
- `FASTAPIPORT`: Server port (default: 8001)

## 🏗️ Architecture

This service is designed as a microservice in a larger system:

- **Input**: Messages from Gmail/Slack (via Ingestor Service)
- **Processing**: AI classification and task generation
- **Output**: Classified messages and generated tasks
- **Storage**: In-memory for development (will connect to MySQL in production)

## 🛠️ Development

### Tech Stack
- **FastAPI**: Modern Python web framework
- **Pydantic v2**: Data validation and serialization
- **Uvicorn**: ASGI server
- **Python 3.8+**: With type hints

### Project Structure
```
ms4-classification/
├── main.py                 # FastAPI application
├── models/                 # Pydantic data models
│   ├── message.py         # Message model
│   ├── classification.py  # Classification model
│   ├── task.py           # Task model
│   └── brief.py          # Brief model
├── services/              # Business logic
│   ├── ai_classifier.py  # AI classification service
│   └── task_generator.py # Task generation service
└── requirements.txt       # Dependencies
```

## 🤝 Team Integration

This service integrates with your team's microservices:

- **Ingestor Service (Sanjay)**: Receives messages from Gmail/Slack
- **Actions Service (Beverly)**: Manages task CRUD operations
- **Database Service (David)**: Provides MySQL database
- **Desktop App (Akhil)**: User interface

## 📝 Example API Calls

### Classify a Message
```bash
curl -X POST "http://localhost:8001/classifications" \
  -H "Content-Type: application/json" \
  -d '{
    "message_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'
```

### Generate Daily Brief
```bash
curl -X POST "http://localhost:8001/briefs" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "date": "2025-01-15"
  }'
```

### Generate Tasks
```bash
curl -X POST "http://localhost:8001/tasks/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "classification_ids": ["71fc7860-02b4-4dfe-8e92-65d430933ccc"],
    "user_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Kill any existing processes on port 8001
lsof -ti:8001 | xargs kill -9
python main.py
```

### Service Not Starting
1. Check Python version: `python --version` (needs 3.8+)
2. Install dependencies: `pip install -r requirements.txt`
3. Check for syntax errors: `python -m py_compile main.py`

### API Not Responding
1. Check if service is running: `curl http://localhost:8001/health`
2. Check logs in terminal where you started the service
3. Verify port 8001 is not blocked by firewall

## 📖 Next Steps

1. **Test the API**: Use the interactive docs at `http://localhost:8001/docs`
2. **Integrate with team**: Connect with other microservices
3. **Add real AI**: Replace mock classification with actual OpenAI API
4. **Database integration**: Connect to MySQL for persistent storage
5. **Production deployment**: Deploy to your cloud platform

---

**Ready to start?** Run `python main.py` and visit `http://localhost:8001/docs` to explore the API! 🚀