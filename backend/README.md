# FastAPI Backend - Code Execution Platform

This is the FastAPI backend for the Code Execution Platform that provides secure Python code execution and terminal functionality.

## Quick Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

#### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
cd backend
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
cd backend
setup.bat
```

#### Option 2: Manual Setup

1. **Create Virtual Environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate Virtual Environment:**
   
   **Linux/macOS:**
   ```bash
   source venv/bin/activate
   ```
   
   **Windows:**
   ```cmd
   venv\Scripts\activate.bat
   ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Running the Server

1. **Activate virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate.bat  # Windows
   ```

2. **Start the FastAPI server:**
   ```bash
   python -m app.main
   ```

   The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

## Project Structure

```
backend/
├── app/
│   ├── api/              # REST API endpoints
│   │   ├── health.py     # Health check endpoints
│   │   └── sessions.py   # Session management
│   ├── core/             # Core utilities
│   │   └── database.py   # Database configuration
│   ├── models/           # SQLAlchemy models
│   │   ├── sessions.py   # Session and command models
│   │   ├── users.py      # User models
│   │   └── submissions.py # Code submission models
│   ├── schemas/          # Pydantic schemas
│   │   └── sessions.py   # Request/response schemas
│   ├── services/         # Business logic
│   │   ├── code_execution.py  # Python code execution
│   │   └── file_manager.py    # File management
│   ├── websockets/       # WebSocket handling
│   │   ├── manager.py    # Connection management
│   │   └── handlers.py   # Message handlers
│   └── main.py          # FastAPI application
├── requirements.txt     # Python dependencies
├── setup.sh            # Setup script (Linux/macOS)
├── setup.bat           # Setup script (Windows)
└── .env                # Environment variables
```

## Features

### REST API Endpoints
- `GET /api/health` - Health check
- `GET /api/sessions` - List all sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session by ID
- `PUT /api/sessions/{id}` - Update session
- `DELETE /api/sessions/{id}` - Delete session

### WebSocket Endpoint
- `WS /ws` - Real-time terminal communication

### Security Features
- Secure Python code execution with timeouts
- File system sandboxing per session
- Path validation to prevent directory traversal
- File size and type restrictions
- Package installation restrictions

### Supported Terminal Commands
- `help` - Show available commands
- `ls` - List files in session directory
- `cat <file>` - Show file contents
- `python <file>` - Execute Python file
- `pip install <package>` - Install allowed packages
- `pwd` - Show current directory
- `clear` - Clear terminal (client-side)

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
PORT=8000
ENVIRONMENT=development
DATABASE_URL=sqlite:///./coding_platform.db
CORS_ORIGIN=http://localhost:3000
PYTHON_TIMEOUT=30
MAX_CODE_SIZE=1048576
SESSION_TIMEOUT=3600
MAX_FILE_SIZE=1048576
```

## Development

### Adding New Dependencies
```bash
# Activate venv first
source venv/bin/activate

# Install new package
pip install new-package

# Update requirements.txt
pip freeze > requirements.txt
```

### Database Migrations
The SQLite database is created automatically when the server starts. For production use, consider switching to PostgreSQL.

## Troubleshooting

### Common Issues

1. **Python not found**: Make sure Python 3.8+ is installed and in your PATH
2. **Permission denied**: On Linux/macOS, make sure setup.sh is executable: `chmod +x setup.sh`
3. **Module not found**: Make sure virtual environment is activated and dependencies are installed
4. **Port already in use**: Change the PORT in `.env` file or kill the process using port 8000

### Logs
The server logs all requests and errors to the console. Check the terminal output for debugging information.

## Testing

The WebSocket connection can be tested using the frontend application or any WebSocket client by connecting to `ws://localhost:8000/ws`.