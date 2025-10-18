# 🕰️ HourglassED

**HourglassED** is a **student-oriented calendar web app** designed to help students organize and plan every aspect of their academic and personal life.  
It combines a powerful **calendar system** with an integrated **AI organizer agent** that intelligently helps users schedule and plan their activities.


## 🧭 Overview

HourglassED allows students to manage and categorize all their events — such as:
- 📘 **Academic**: exams, courses, study sessions  
- 💼 **Work**: meetings, shifts, part-time schedules  
- 💬 **Personal**: appointments, reminders  
- 🎭 **Extracurricular**: volunteering, club events  
- ➕ **Custom event types** users can create themselves

where they can even share their events (like study sessions) with friends to motivate each other!

In addition, HourglassED introduces an **Organizer Agent** powered by **LangGraph** and **FastMCP**, which:
- Reads the user's current calendar  
- Suggests study or event schedules  
- Allows user feedback before committing changes  
- Lets users skip or cancel plans safely

All changes go through a **proposal/approval** pipeline — ensuring the AI never changes the calendar without the user’s consent.


### 🧠 Example Prompt
*(assuming “Image Processing Midterm” already exists in the calendar, otherwise agent will pause to ask about date)*

> “I want you to help me organize multiple study sessions for my Image Processing midterm.  
> I want a total of 15 study hours until the day of the exam.  
> DO NOT put any study sessions during the same day of the exam.”


### ⚙️ Tech Stack
**Backend**
- FastAPI – high-performance Python web framework  
- Celery – background task queue  
- Redis – Celery broker  
- SQLAlchemy – ORM for MySQL  
- Pydantic – data validation  
- LangGraph – LLM workflow orchestration  

**MCP SERVER**
- FastMCP – agent-to-backend communication 

**Frontend**
- React + Vite  
- TypeScript  
- TailwindCSS  

**Database**
- MySQL


## 🏗️ Architecture

The project consists of **three main components**:

```
HourglassED/
├── backend/              # FastAPI backend (MySQL, Celery, LangGraph)
│   ├── agent/            # AI agent (LangGraph workflow)
│   ├── models/           # SQLAlchemy ORM models
│   ├── routers/          # FastAPI route handlers
│   ├── schemas/          # Pydantic data schemas
│   ├── utils/            # Helper utilities
│   ├── main.py           # FastAPI app entry point
│   ├── tasks.py          # Celery background tasks
│   ├── celery_app.py     # Celery setup
│   └── requirements.txt  # Backend dependencies
│
├── frontend/             # React + TypeScript frontend
│   ├── src/              # Components, pages, hooks, utils
│   ├── public/           # Static assets (icons, images)
│   ├── package.json      # Frontend dependencies
│   └── vite.config.ts    # Build configuration
│
├── hourglassed-mcp/      # FastMCP server (Agent tools)
│   ├── server.py         # MCP server entry point
│   ├── auth.py           # Authentication logic
│   ├── schemas.py        # Data schemas
│   └── requirements.txt  # MCP dependencies
│
├── db/                   # Database files
│   ├── schema.sql        # SQL schema
│   └── seed.sql          # Initial data
│
└── scripts/              # Bash scripts
    ├── start_all.sh
    ├── start_backend.sh
    ├── start_celery.sh
    ├── start_frontend.sh
    └── start_all.sh

```


## 🚀 Quick Start
### 1) Clone and set up environments

```bash
git clone https://github.com/ShamsJarrar/HourglassED.git
cd HourglassED
```

**Backend (FastAPI):**
```bash
cd backend
# create virtual environment
python -m venv venv
source venv/Scripts/activate

# instal dependencies
pip install -r requirements.txt

# Open .env and set all variables
cp .env.example .env              # create your local env file

# Create the mysql database (example)
# mysql -u root -p -e "CREATE DATABASE hourglassed_db;"

cd ..
```

**MCP server:**
```bash
cd hourglassed-mcp

# create virtual environment
python -m venv .mcpenv
source .mcpenv/Scripts/activate

# install dependencies
pip install -r requirements.txt

# Open .env and set all variables
cp .env.example .env              # match values required by the MCP server

cd ..
```

> Tip: keep Docker Desktop running (needed for Redis).


### 2) Run the app (in order)

**A. MCP server**
```bash
cd hourglassed-mcp
source .mcpenv/Scripts/activate
python server.py
```

**B. Celery + Redis (from project root)**
```bash
# Start Redis (first time)
docker run -d -p 6379:6379 --name redis redis
# Or start it if it already exists
docker start redis

# Start Celery worker & beat
cd backend
source venv/Scripts/activate
celery -A tasks worker --loglevel=info --pool=solo 
celery -A tasks beat --loglevel=info
```

**C. Backend (FastAPI)**
```bash
cd backend
source venv/Scripts/activate
uvicorn main:app --reload
```

**D. Frontend**
```bash
cd frontend
npm install
npm run dev
```

### 3) Or start everything via scripts

From project root (Git Bash on Windows):

```bash
chmod +x scripts/*.sh
./scripts/start_all.sh
```
This launches: MCP → Redis → Celery (worker & beat) → FastAPI → React.


## ⚡Note
Hope you enjoy the app!!!
