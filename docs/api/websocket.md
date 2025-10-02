# WebSocket API

The WebSocket API provides real-time terminal communication for code execution and interactive shell operations. The backend manages Kubernetes pods for each session, providing isolated execution environments.

## Connection

**Endpoint:** `ws://{backend-service}/api/terminal/ws/{session_id}`

**Path Parameters:**
- `session_id` (required): Unique session identifier for the workspace

**Example:** `ws://localhost:8002/api/terminal/ws/user_1_ws_abc123_1234567890_uuid`

## Connection Flow

1. Client establishes WebSocket connection with session_id in path
2. Backend checks if execution pod exists for session
3. If no pod exists, backend creates new Kubernetes pod with PVC
4. Backend waits for pod to reach "Running" and "Ready" status
5. Files from database are synced to pod filesystem
6. Connection established, terminal commands can be sent
7. On disconnect, pod may be cleaned up or kept alive for reconnection

## Message Format

### Client to Server
The client sends terminal commands as plain text strings (not JSON).

**Example:**
```
ls -la
```

```
python main.py
```

```
pip install requests
```

### Server to Client
The server responds with terminal output as plain text strings.

**Example Response:**
```
total 12
drwxr-xr-x 2 root root 4096 Jan  1 00:00 .
drwxr-xr-x 3 root root 4096 Jan  1 00:00 ..
-rw-r--r-- 1 root root   45 Jan  1 00:00 main.py
```

## Command Execution

All commands are executed directly in the Kubernetes pod using `kubectl exec`. The terminal behaves like a real bash shell.

### Supported Commands

**File Operations:**
```bash
ls -la                    # List files
cat main.py              # View file contents
touch newfile.py         # Create file
echo "hello" > file.txt  # Write to file
rm file.txt              # Delete file
cp source.py dest.py     # Copy file
mv old.py new.py         # Move/rename file
```

**Python Execution:**
```bash
python main.py                  # Run Python script
python -c "print('hello')"     # Execute Python inline
pip install requests           # Install packages
pip list                       # List installed packages
```

**Node.js Execution:**
```bash
node script.js                 # Run Node.js script
npm install express            # Install npm packages
npm list                       # List installed packages
```

**System Commands:**
```bash
pwd                    # Print working directory
cd subdirectory        # Change directory
mkdir newfolder        # Create directory
wget https://...       # Download files
curl https://...       # Make HTTP requests
git clone https://...  # Clone repositories
```

### File Synchronization

After certain commands, the backend automatically syncs changes back to the database:

**Commands that trigger sync:**
- File creation: `touch`, `echo >`, `cat >`
- File modification: `python`, `node`, `vim`, `nano`
- Package installation: `pip install`, `npm install`
- Downloads: `wget`, `curl`, `git clone`
- Any command with redirection: `>`, `>>`, `tee`

**How sync works:**
1. Backend detects file-modifying command
2. Lists all files in pod workspace (`ls -R`)
3. Reads content of each file (`cat`)
4. Updates or creates workspace_items in database
5. Client file tree automatically refreshes

## Session Management

The WebSocket connection automatically manages:
- Kubernetes pod creation and lifecycle
- Session isolation via separate pods
- Pod cleanup on disconnect
- PersistentVolumeClaim (PVC) for file persistence
- Readiness checks before accepting commands
- Bidirectional file sync (DB ↔ Pod)

## Error Handling

### Pod Not Ready
If commands are sent before pod is ready:
```
Error: Pod is not ready yet. Current status: Pending
Please wait...
```

Backend waits up to 60 seconds for pod to become ready.

### Command Execution Errors
Errors are returned as plain text from the pod:
```
python syntax_error.py
  File "syntax_error.py", line 1
    print("hello"
                ^
SyntaxError: invalid syntax
```

### Pod Creation Failures
```
Error: Failed to create execution pod
Details: Insufficient resources in cluster
```

### Connection Errors
```
Error: WebSocket connection failed
Please refresh and try again
```

## Pod Lifecycle

1. **Creation**: Pod created when WebSocket connection established
   - Name: `exec-{session_id}`
   - Image: `rraup12/code-execution:latest`
   - PVC: 1Gi storage attached
2. **Initialization**: Pod starts, installs packages, becomes ready (10-30 seconds)
3. **File Sync**: Database files synced to pod `/app/workspace/`
4. **Active**: Pod accepts commands via `kubectl exec`
5. **Sync Back**: File changes automatically synced to database
6. **Cleanup**: Pod deleted when session ends (manual or automatic)

## Security

- Each user gets isolated Kubernetes pod
- File system is sandboxed within pod (no host access)
- Network access available (for pip, npm, wget, etc.)
- Resource limits: 500m CPU, 512Mi memory per pod
- RBAC controls backend pod's Kubernetes API access
- Session IDs prevent cross-user access
- PVCs provide storage isolation

## Usage Example

### JavaScript/TypeScript Client

```typescript
const sessionId = 'user_1_ws_abc123_1234567890_uuid';
const ws = new WebSocket(`ws://localhost:8002/api/terminal/ws/${sessionId}`);

ws.onopen = () => {
  // Send initial command
  ws.send('ls -la\n');
};

ws.onmessage = (event) => {
  // Receive plain text terminal output
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Send commands as plain text strings
ws.send('python main.py\n');
ws.send('pip install requests\n');
ws.send('echo "Hello" > test.txt\n');
```

### React + xterm.js Integration

```typescript
import { Terminal } from 'xterm';
import { useEffect, useRef } from 'react';

function TerminalComponent({ sessionId }: { sessionId: string }) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const term = useRef<Terminal | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!terminalRef.current) return;

    // Initialize xterm.js
    term.current = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'monospace',
    });
    term.current.open(terminalRef.current);

    // Connect WebSocket
    ws.current = new WebSocket(
      `ws://localhost:8002/api/terminal/ws/${sessionId}`
    );

    // Send terminal input to backend
    term.current.onData((data) => {
      ws.current?.send(data);
    });

    // Display output from backend
    ws.current.onmessage = (event) => {
      term.current?.write(event.data);
    };

    return () => {
      term.current?.dispose();
      ws.current?.close();
    };
  }, [sessionId]);

  return <div ref={terminalRef} style={{ height: '500px' }} />;
}
```

## Implementation Details

### Backend Handler
**File:** `backend/app/websockets/handlers.py`

**Key Functions:**
- `handle_terminal_command()`: Main command handler
- `sync_pod_changes_to_database()`: Syncs pod files to DB after commands
- Uses `container_manager` to manage pod lifecycle
- Uses `file_sync_service` for bidirectional sync

### Pod Management
**File:** `backend/app/services/kubernetes_client.py`

**Key Functions:**
- `create_pod()`: Creates Kubernetes pod with PVC
- `wait_for_pod_ready()`: Polls pod status until ready
- `exec_command()`: Executes command in pod via kubectl
- `delete_pod()`: Cleans up pod and resources

### File Sync Service
**File:** `backend/app/services/file_sync.py`

**Key Functions:**
- `load_files_to_pod()`: DB → Pod (on session start)
- `sync_pod_to_database()`: Pod → DB (after modifications)
- Maintains directory structure
- Handles binary and text files