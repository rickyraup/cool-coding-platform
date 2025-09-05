# Code Execution Platform

A web-based development environment with integrated terminal functionality. Users can write Python 3 code in an editor and execute it directly through the integrated terminal interface.

## Features

- 🖥️ **Code Editor**: Text editor with Python syntax highlighting
- 📟 **Terminal Interface**: Command-line interface supporting Python execution, package installation, and file operations
- 🔒 **Secure Execution**: Isolated Python environment for safe code execution
- 💾 **Session Persistence**: Save and restore coding sessions
- 👥 **Code Submission**: Submit code for review and feedback (bonus feature)
- 📊 **Python Libraries**: Includes pandas, scipy, numpy, and matplotlib

## Tech Stack

### Frontend
- **Framework**: Next.js 15.5.2 with TypeScript
- **Styling**: TailwindCSS v4
- **Build Tool**: Turbopack

### Backend
- **Runtime**: Node.js with TypeScript
- **Framework**: Express.js
- **WebSocket**: ws for real-time communication
- **Process Management**: node-pty for command execution

### Shared
- **Types**: Shared TypeScript interfaces and types
- **Utils**: Common utilities and constants

## Project Structure

```
├── frontend/              # Next.js frontend application
│   ├── src/
│   │   └── app/          # App Router pages and layouts
│   ├── public/           # Static assets
│   └── package.json      # Frontend dependencies
├── backend/              # Node.js backend service
│   ├── src/
│   │   ├── api/          # REST API routes
│   │   ├── services/     # Business logic services
│   │   ├── models/       # Data models
│   │   ├── utils/        # Backend utilities
│   │   └── middleware/   # Express middleware
│   ├── tests/            # Backend tests
│   └── package.json      # Backend dependencies
├── shared/               # Shared code between frontend and backend
│   ├── types/           # TypeScript type definitions
│   ├── constants/       # Shared constants
│   └── utils/           # Shared utilities
├── docs/                # Project documentation
│   ├── api/            # API documentation
│   ├── architecture/   # Architecture diagrams
│   └── deployment/     # Deployment guides
└── README.md           # This file
```

## Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- npm or yarn

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development
```bash
cd backend
npm install
cp .env.example .env  # Configure environment variables
npm run dev
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:
- `PORT`: Backend server port (default: 3001)
- `DATABASE_URL`: Database connection string
- `JWT_SECRET`: Secret for JWT token signing
- `PYTHON_SANDBOX_PATH`: Path for Python code execution

## Security

- All Python code execution happens in an isolated environment
- File system access is limited to user session directories
- Input validation on all commands
- Rate limiting on API endpoints
- Session isolation between users

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
