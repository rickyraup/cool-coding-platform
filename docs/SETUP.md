# Code Execution Platform - Setup Guide

## Prerequisites

### System Requirements
- **Node.js:** 18+ (for frontend)
- **Python:** 3.9+ (for backend)
- **PostgreSQL:** 14+ (database)
- **Docker:** 20+ (for code execution containers)
- **Git:** For version control

### Environment Setup

## Backend Setup

### 1. Database Setup
```bash
# Install PostgreSQL (macOS with Homebrew)
brew install postgresql
brew services start postgresql

# Create database and user
createdb coolcoding
createuser -s coolcoding_user
```

### 2. Backend Installation
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Database Migration
```bash
# Run migrations to set up database schema
python -m app.core.database
```

### 4. Start Backend Server
```bash
# Development mode
python -m app.main

# The API will be available at http://localhost:8002
```

## Frontend Setup

### 1. Frontend Installation
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API URL
```

### 2. Start Development Server
```bash
# Development mode with Turbopack
npm run dev

# The app will be available at http://localhost:3000
```

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://coolcoding_user:password@localhost/coolcoding
ENVIRONMENT=development
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8002
```

## Development Workflow

### 1. Start Services
```bash
# Terminal 1: Database
brew services start postgresql

# Terminal 2: Backend
cd backend && source venv/bin/activate && python -m app.main

# Terminal 3: Frontend
cd frontend && npm run dev
```

### 2. Access Application
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8002
- **API Docs:** http://localhost:8002/docs

## Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

### Frontend Linting
```bash
cd frontend
npm run lint
npm run type-check
```

## Docker Setup (Optional)

### Container-based Development
```bash
# Build and run with Docker Compose
docker-compose up --build

# For testing with isolated database
docker-compose -f docker-compose.test.yml up --build
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL is running
   - Verify database credentials in .env
   - Check if database exists

2. **Port Conflicts**
   - Backend default: 8002
   - Frontend default: 3000
   - Change ports in configuration if needed

3. **Docker Issues**
   - Ensure Docker daemon is running
   - Check container logs for errors
   - Verify file permissions for volumes

### Logs and Debugging
- **Backend logs:** Check console output
- **Frontend logs:** Check browser console
- **Database logs:** Check PostgreSQL logs
- **Container logs:** `docker logs <container_name>`

## Production Deployment

### Environment Preparation
1. Set up production PostgreSQL database
2. Configure environment variables for production
3. Build frontend for production: `npm run build`
4. Set up reverse proxy (nginx/Apache)
5. Configure SSL certificates

### Security Considerations
- Use strong database passwords
- Enable HTTPS in production
- Configure CORS properly
- Review container security settings
- Implement rate limiting

## Additional Resources

- [API Documentation](http://localhost:8002/docs) (when running)
- [Architecture Overview](./architecture/ARCHITECTURE.md)
- [Database Schema](./database/DATABASE.md)
- [Feature Guide](./FEATURES.md)