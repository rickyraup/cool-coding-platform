┌────────────────────────────┐
│        Client (UI)         │
│                            │
│  - React + TypeScript      │
│  - Monaco Editor           │
│  - xterm.js Terminal       │
│  - WebSocket client        │
└────────────┬───────────────┘
             │ HTTP / WS
             ▼
┌────────────────────────────┐
│         Backend API        │
│     (FastAPI)   │
│                            │
│  ┌──────────────────────┐  │
│  │   Session Manager     │◄─┐
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │  Terminal Proxy       │◄─┐ WebSocket input/output
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ Docker Manager        │◄─┐ Starts/stops containers
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ File Sync / Storage   │◄─┐ Reads/writes to mounted dir
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │  Auth & User Service  │  │
│  └──────────────────────┘  │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│      PostgreSQL / DB       │
│                            │
│  - Users                   │
│  - Sessions                │
│  - Submissions (reviews)   │
│  - File metadata (optional)│
└────────────────────────────┘

             ▼
┌────────────────────────────┐
│     File Storage (host)    │
│  (/sessions/session-id/)   │
│                            │
│  - Mounted into Docker     │
│  - Shared with editor & fs │
└────────────────────────────┘

             ▼
┌────────────────────────────┐
│     Docker Containers      │
│                            │
│  - Python 3.11 base image  │
│  - Has pandas, scipy, etc. │
│  - Executes all code       │
│  - Handles shell commands  │
└────────────────────────────┘
