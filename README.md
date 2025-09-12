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

**Quick Setup:**
```bash
cd backend
./setup.sh  # Linux/macOS
# or setup.bat on Windows
```

**Manual Setup:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate.bat on Windows
pip install -r requirements.txt
python -m app.main
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


High-Risk Security Concerns

  1. Container Escape

  - Risk: User code could exploit Docker vulnerabilities to access host system
  - Mitigation:
    - Use latest Docker version with security patches
    - Run containers with --security-opt=no-new-privileges
    - Use AppArmor/SELinux profiles
    - Never run containers in privileged mode

  2. Resource Exhaustion (DoS)

  - Risk: Infinite loops, memory bombs, fork bombs
  - Mitigation:
  --memory=512m --memory-swap=512m
  --cpus=1 --pids-limit=50
  --ulimit nofile=100 --ulimit nproc=50

  3. Persistent Storage Attacks

  - Risk: Malicious files persisting between sessions
  - Mitigation:
    - Use --rm flag for automatic cleanup
    - Mount temporary directories only: --tmpfs /tmp
    - Scan uploaded files before execution

  4. Network-Based Attacks

  - Risk: Data exfiltration, external service abuse
  - Mitigation:
    - Use --network=none for complete isolation
    - If network needed: custom bridge with firewall rules
    - Block all outbound except whitelisted package repos

  Medium-Risk Concerns

  5. Host Information Disclosure

  - Risk: Access to host metadata, Docker socket
  - Mitigation:
    - Never mount /var/run/docker.sock
    - Use read-only filesystem: --read-only
    - Minimal base image (python:3.11-slim)

  6. Timing/Side-Channel Attacks

  - Risk: Session interference, resource timing attacks
  - Mitigation:
    - Randomized session IDs
    - Container name randomization
    - Resource quotas per user

  Implementation Security Strategy

  # Container Security Configuration
  CONTAINER_CONFIG = {
      'image': 'coding-platform:python311',
      'command': ['/bin/bash'],
      'detach': True,
      'remove': True,  # Auto-cleanup
      'read_only': True,  # Read-only filesystem
      'security_opt': ['no-new-privileges'],
      'mem_limit': '512m',
      'memswap_limit': '512m',
      'cpu_count': 1,
      'pids_limit': 50,
      'network_mode': 'none',  # No network access
      'user': '1000:1000',  # Non-root user
      'working_dir': '/app',
      'volumes': {
          '/tmp/session-{session_id}': {'bind': '/app', 'mode': 'rw'}
      },
      'environment': {
          'PYTHONPATH': '/app',
          'HOME': '/app'
      }
  }

  Runtime Security Monitoring

  - Container resource usage tracking
  - Command execution logging
  - File system change monitoring
  - Automatic container termination after 30 minutes
  - Rate limiting on container creation per user

  Validation & Input Sanitization

  - Filename validation (no ../, special chars)
  - Code size limits (max 1MB per file)
  - File type restrictions (Python, text files only)
  - Command length limits in terminal
