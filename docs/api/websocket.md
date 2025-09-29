# WebSocket API

The WebSocket API provides real-time terminal communication for code execution and interactive shell operations.

## Connection

**Endpoint:** `ws://localhost:8001/ws`

**Query Parameters:**
- `user_id` (optional): User ID for authentication

## Connection Flow

1. Client establishes WebSocket connection
2. Server sends connection confirmation
3. Client can send commands and receive real-time responses
4. Server manages session isolation and container lifecycle

## Message Format

### Client to Server
```json
{
  "type": "execute_code",
  "sessionId": "workspace-uuid",
  "code": "print('Hello World')",
  "filename": "main.py"
}
```

### Server to Client
```json
{
  "type": "execution_result",
  "success": true,
  "output": "Hello World\n",
  "timestamp": "2024-01-01T00:00:00Z",
  "sessionId": "workspace-uuid"
}
```

## Message Types

### Execute Code
Execute Python code in the workspace container.

**Client Message:**
```json
{
  "type": "execute_code",
  "sessionId": "workspace-uuid",
  "code": "import numpy as np\nprint(np.array([1,2,3]))",
  "filename": "script.py"
}
```

**Server Response:**
```json
{
  "type": "execution_result",
  "success": true,
  "output": "[1 2 3]\n",
  "error": null,
  "timestamp": "2024-01-01T00:00:00Z",
  "sessionId": "workspace-uuid"
}
```

### Terminal Command
Execute terminal commands in the workspace.

**Client Message:**
```json
{
  "type": "terminal_command",
  "sessionId": "workspace-uuid",
  "command": "ls -la"
}
```

**Server Response:**
```json
{
  "type": "terminal_output",
  "output": "total 8\ndrwxr-xr-x 2 root root 4096 Jan  1 00:00 .\ndrwxr-xr-x 3 root root 4096 Jan  1 00:00 ..\n-rw-r--r-- 1 root root   20 Jan  1 00:00 main.py\n",
  "sessionId": "workspace-uuid"
}
```

### File Save
Save file content to the workspace.

**Client Message:**
```json
{
  "type": "save_file",
  "sessionId": "workspace-uuid",
  "filename": "main.py",
  "content": "print('Updated content')"
}
```

**Server Response:**
```json
{
  "type": "save_result",
  "success": true,
  "message": "File saved successfully",
  "filename": "main.py",
  "sessionId": "workspace-uuid"
}
```

## Session Management

The WebSocket connection automatically manages:
- Container creation and lifecycle
- Session isolation between users
- Container cleanup on disconnect
- File system persistence per session

## Error Handling

### Execution Errors
```json
{
  "type": "execution_result",
  "success": false,
  "output": "",
  "error": "SyntaxError: invalid syntax",
  "timestamp": "2024-01-01T00:00:00Z",
  "sessionId": "workspace-uuid"
}
```

### System Errors
```json
{
  "type": "error",
  "message": "Container failed to start",
  "error": "Docker daemon not responding",
  "sessionId": "workspace-uuid"
}
```

## Container Lifecycle

1. **Connection**: Container starts when first command is sent
2. **Active**: Container remains active during WebSocket connection
3. **Idle**: Container may be paused after inactivity
4. **Cleanup**: Container destroyed when all connections close

## Security

- Each user gets isolated container environment
- File system is sandboxed per session
- Network access is restricted
- Resource limits prevent abuse
- Session IDs prevent cross-user access

## Usage Example

```javascript
const ws = new WebSocket('ws://localhost:8001/ws?user_id=123');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Execute Python code
ws.send(JSON.stringify({
  type: 'execute_code',
  sessionId: 'my-workspace-uuid',
  code: 'print("Hello from Python")',
  filename: 'main.py'
}));

// Run terminal command
ws.send(JSON.stringify({
  type: 'terminal_command',
  sessionId: 'my-workspace-uuid',
  command: 'pip install numpy'
}));
```