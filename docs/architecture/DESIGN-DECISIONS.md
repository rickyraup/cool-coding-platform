# System Design Decisions & Tradeoffs

## Overview

This document outlines the key architectural decisions made in building the Code Execution Platform, the tradeoffs involved, and the rationale behind each choice. Understanding these decisions helps explain why the system works the way it does and what alternatives were considered.

---

## Core Architecture Decisions

### 1. Kubernetes-Based Execution Environment

**Decision:** Use Kubernetes pods for isolated code execution rather than Docker containers, VMs, or serverless functions.

**Rationale:**
- **Production-Ready:** Kubernetes provides battle-tested orchestration for container workloads
- **Resource Management:** Built-in resource limits, quotas, and autoscaling
- **Isolation:** Network and process isolation between user sessions
- **Portability:** Works on any Kubernetes cluster (local kind, DigitalOcean, AWS, GCP, Azure)
- **Ecosystem:** Rich tooling for monitoring, logging, and observability

**Tradeoffs:**

| ✅ Pros | ❌ Cons |
|---------|---------|
| Strong isolation between users | Slower startup time (~10-20s for pod) |
| Production-grade orchestration | Steeper learning curve than Docker Compose |
| Horizontal scaling built-in | More complex local development setup |
| Industry standard | Higher infrastructure cost for small deployments |
| RBAC and security policies | Requires Kubernetes knowledge to debug |

**Alternatives Considered:**
- **Docker containers via API:** Simpler but lacks production-grade orchestration
- **Serverless (Lambda/Cloud Run):** Cheaper at low scale but cold starts, execution time limits
- **VMs:** Better isolation but much slower startup, higher resource overhead
- **Process isolation (chroot/seccomp):** Lightweight but weaker security guarantees

**Why This Works:**
For a multi-user code execution platform, the overhead of Kubernetes is justified by the security, scalability, and operational maturity it provides. The 10-20s pod startup is acceptable for a development environment where users work for minutes to hours per session.

---

### 2. Database as Source of Truth for Files

**Decision:** Store all file contents in PostgreSQL (`workspace_items` table) and sync bidirectionally with pod filesystems.

**Rationale:**
- **Durability:** Files persist even if pods are deleted or crash
- **Consistency:** Single source of truth prevents sync conflicts
- **Backup:** Database backups automatically include all user code
- **Multi-Session:** Users can switch between sessions without losing work
- **Atomic Updates:** Database transactions ensure file saves are atomic

**Tradeoffs:**

| ✅ Pros | ❌ Cons |
|---------|---------|
| Files survive pod restarts | Extra latency on file saves (~1-2s sync) |
| Easy backups and recovery | Database size grows with file count |
| No data loss on pod deletion | Binary files inefficient in TEXT columns |
| Queryable file metadata | Additional complexity in sync logic |
| Session switching without data loss | Can't use native git in pod (files ephemeral) |

**Alternatives Considered:**
- **PVC-only storage:** Faster but data lost if PVC deleted, harder to backup
- **S3/Object storage:** Cheaper at scale but more complex, higher latency
- **Git repository per session:** Native version control but complex to manage
- **Hybrid:** Critical files in DB, temp files in PVC (rejected as too complex)

**Why This Works:**
For a development environment with relatively small codebases (<100 files, <10MB total), database storage is simple and reliable. The 1-2s sync delay is acceptable for saves, and users get guaranteed durability without thinking about backups.

**File Sync Architecture:**
```
User saves file in editor
    ↓
POST /api/workspace/{uuid}/file/{filename}
    ↓
Backend saves to workspace_items table
    ↓
sync_file_to_pod() creates tar archive
    ↓
kubectl exec to write tar to /app/ in pod
    ↓
File now in: DB (source of truth) + Pod (execution environment)
```

---

### 3. WebSocket for Terminal Communication

**Decision:** Use WebSocket protocol with JSON messages for real-time terminal I/O instead of HTTP polling or SSE.

**Rationale:**
- **Bi-directional:** Client and server can both initiate messages
- **Low Latency:** No HTTP overhead for each keystroke
- **Efficient:** Single persistent connection instead of polling
- **Real-time:** Updates appear instantly in terminal
- **Standard:** xterm.js has built-in WebSocket support

**Tradeoffs:**

| ✅ Pros | ❌ Cons |
|---------|---------|
| True real-time updates | More complex than HTTP API |
| Low latency (<100ms) | Connection state must be managed |
| Bi-directional communication | Can't use HTTP caching |
| Efficient bandwidth usage | Load balancers need WebSocket support |
| Works with xterm.js | Debugging harder than HTTP requests |

**Alternatives Considered:**
- **HTTP polling:** Simple but wasteful, high latency
- **Server-Sent Events (SSE):** One-way only, requires separate upload channel
- **HTTP/2 streams:** Not widely supported in clients yet
- **gRPC:** More complex, no browser support without proxy

**Why This Works:**
For an interactive terminal, WebSocket is the industry standard. The added complexity is offset by excellent library support (xterm.js on frontend, FastAPI WebSocket on backend) and the user experience is dramatically better than polling.

---

### 4. Horizontal Pod Autoscaler (HPA) for Backend Scaling

**Decision:** Use Kubernetes HPA to automatically scale backend pods from 2-10 based on CPU/memory metrics.

**Rationale:**
- **Automatic:** No manual intervention needed during traffic spikes
- **Cost-Effective:** Scales down during low usage (e.g., nights, weekends)
- **Responsive:** Scales up immediately when CPU > 70% or memory > 80%
- **Stable:** 5-minute cooldown prevents thrashing on scale-down
- **Production-Ready:** Standard Kubernetes feature, well-tested

**Configuration:**
```yaml
minReplicas: 2   # Always running for redundancy
maxReplicas: 10  # Prevents runaway scaling
targetCPUUtilizationPercentage: 70
targetMemoryUtilizationPercentage: 80
behavior:
  scaleUp:
    stabilizationWindowSeconds: 0   # Immediate scale-up
    policies:
    - type: Percent
      value: 100  # Double pods or +2, whichever is more
  scaleDown:
    stabilizationWindowSeconds: 300  # 5 min cooldown
    policies:
    - type: Percent
      value: 50   # Remove 50% or 1 pod, whichever is less
```

**Tradeoffs:**

| ✅ Pros | ❌ Cons |
|---------|---------|
| Automatic load handling | CPU/memory metrics lag actual user count |
| Lower cost at low usage | Scaling events can cause brief latency spikes |
| No manual intervention | Requires metrics-server in cluster |
| Handles traffic spikes | Can over-provision during gradual ramps |
| Prevents overload | Doesn't scale based on WebSocket connections |

**Alternatives Considered:**
- **Fixed replicas:** Simple but wasteful or insufficient
- **Manual scaling:** Requires constant monitoring
- **Custom metrics (WebSocket count):** More accurate but complex to implement
- **Predictive scaling:** Overkill for current usage patterns

**Why This Works:**
For a development platform with variable usage (high during work hours, low at night), HPA provides good balance between cost and availability. The 2-10 replica range handles 10-40 concurrent users comfortably while keeping costs reasonable.

**Capacity Analysis:**
- **2 pods:** 10-15 users (baseline)
- **5 pods:** 25-30 users (moderate load)
- **10 pods:** 40-50 users (peak capacity)

---

### 5. PersistentVolumeClaims for Execution Pod Storage

**Decision:** Each execution pod gets a 1Gi PVC mounted at `/app/` rather than using emptyDir (ephemeral) storage.

**Rationale:**
- **Persistence:** Files survive pod restarts (e.g., during cluster node maintenance)
- **Performance:** Faster file I/O than syncing to/from database for every command
- **Compatibility:** Works with tools that expect persistent filesystem (pip cache, node_modules)
- **Isolation:** Each session gets dedicated storage, no cross-contamination

**Tradeoffs:**

| ✅ Pros | ❌ Cons |
|---------|---------|
| Faster file operations | Higher infrastructure cost (storage) |
| Survives pod restarts | PVCs take time to provision (~2-5s) |
| pip/npm caching works | Must explicitly delete PVCs on cleanup |
| Feels like real filesystem | More complex pod creation logic |
| Better for installed packages | Storage quota must be monitored |

**Alternatives Considered:**
- **emptyDir (ephemeral):** Cheaper but lost on pod restart, no caching
- **Shared PVC:** Cost-effective but security risk, no isolation
- **NFS/hostPath:** Complex, not portable across clusters
- **No PVC (DB-only):** Simpler but every file operation hits database

**Why This Works:**
1Gi PVC per session is affordable (~$0.10/month per active user on DigitalOcean) and provides a much better developer experience. Package installs are cached, file operations are fast, and pods can survive node maintenance without data loss.

**Storage Breakdown:**
```
1Gi PVC per session
  ├─ Python 3.11 base (~200MB)
  ├─ pandas, scipy, numpy (~100MB)
  ├─ User code (~1-10MB typical)
  ├─ pip cache (~50-100MB)
  └─ Working space (~500MB available)
```

---

### 6. Background Task Manager for Cleanup

**Decision:** Implement background tasks that run on a schedule to clean up idle sessions and orphaned pods.

**Rationale:**
- **Resource Efficiency:** Automatically removes unused pods to save costs
- **Self-Healing:** Cleans up orphaned resources from crashes
- **User Experience:** No manual cleanup required
- **Cost Control:** Prevents runaway pod creation from bugs

**Implementation:**
```python
# Runs every 60 seconds
async def cleanup_idle_sessions():
    for session in active_sessions:
        idle_time = now() - session.last_activity
        total_time = now() - session.created_at

        if idle_time > 30 minutes:
            delete_pod_and_pvc(session)
        elif total_time > 2 hours:
            delete_pod_and_pvc(session)
```

**Tradeoffs:**

| ✅ Pros | ❌ Cons |
|---------|---------|
| Automatic cleanup | Can delete active sessions if user idle |
| Prevents resource leaks | Fixed thresholds may not suit all users |
| Self-healing after crashes | Background task adds complexity |
| Cost savings | Timer inaccuracy on pod restarts |
| No manual intervention | Hard to debug when session disappears |

**Parameters:**
- **Idle Threshold:** 30 minutes (no terminal commands, no file saves)
- **Max Session Lifetime:** 2 hours (hard limit)
- **Cleanup Frequency:** 60 seconds
- **Startup Cleanup:** Removes orphaned pods from previous crashes

**Alternatives Considered:**
- **Manual cleanup:** Simple but users forget, resources leak
- **Time-to-Live (TTL) controller:** Kubernetes feature but requires 1.21+
- **External cron job:** Works but less integrated with backend state
- **No cleanup:** Unacceptable due to cost

**Why This Works:**
For a shared development platform, automatic cleanup is essential to keep costs manageable. The 30-minute idle threshold is generous enough for users taking breaks but aggressive enough to prevent waste. The 2-hour hard limit prevents long-running compute jobs from hogging resources.

---

### 7. FastAPI Backend Framework

**Decision:** Use FastAPI for the backend API instead of Flask, Django, or Express.js.

**Rationale:**
- **Async/Await:** Native async support for WebSockets and concurrent requests
- **Type Safety:** Built-in Pydantic validation and type hints
- **Performance:** Faster than Flask, comparable to Node.js/Go
- **Documentation:** Auto-generated OpenAPI/Swagger docs
- **Modern:** Based on Python 3.6+ type hints and ASGI standard

**Tradeoffs:**

| ✅ Pros | ❌ Cons |
|---------|---------|
| Fast (async) | Newer, smaller ecosystem than Flask |
| Type-safe | Requires Python 3.9+ |
| Auto-generated docs | Learning curve for async Python |
| WebSocket support | More opinionated than Flask |
| Active development | Some libraries don't support ASGI |

**Alternatives Considered:**
- **Flask:** Simpler but slower (WSGI, not async), less type-safe
- **Django:** More features but heavier, overkill for our needs
- **Express.js:** Good async but team prefers Python, less type-safe
- **Go (Gin/Echo):** Faster but less familiar to team, smaller data science ecosystem

**Why This Works:**
For a WebSocket-heavy application with concurrent users, FastAPI's async support is crucial. The auto-generated API docs save time, and Pydantic validation catches bugs early. Python's data science ecosystem (pandas, numpy) is valuable for users.

---

### 8. PostgreSQL over NoSQL

**Decision:** Use PostgreSQL (Supabase managed) for all data storage instead of MongoDB, DynamoDB, or other NoSQL databases.

**Rationale:**
- **Relational:** User → Sessions → Files is naturally hierarchical
- **ACID:** Transactions ensure data consistency
- **Mature:** 30+ years of development, well-understood
- **Tooling:** Excellent admin tools, ORMs, migration frameworks
- **Supabase:** Managed hosting with backups, monitoring, scaling

**Tradeoffs:**

| ✅ Pros | ❌ Cons |
|---------|---------|
| ACID transactions | Vertical scaling limits |
| Strong consistency | Schema migrations required |
| SQL querying | More complex than key-value stores |
| Mature ecosystem | Can be overkill for simple data |
| Easy to backup | Joins can be slow at massive scale |

**Alternatives Considered:**
- **MongoDB:** Schema-less but less consistent, weaker transactions
- **DynamoDB:** Serverless but vendor lock-in, complex pricing
- **SQLite:** Simple but no concurrency, not production-ready
- **Firebase:** Easy but expensive, vendor lock-in

**Why This Works:**
Our data is inherently relational (users have many sessions, sessions have many files). PostgreSQL's foreign keys, indexes, and transactions make the code simpler and safer. Supabase provides managed hosting so we don't worry about backups or scaling.

**Schema Optimizations:**
- **session_uuid denormalized** in workspace_items for faster pod sync (avoids JOIN)
- **full_path computed** and stored for faster file lookups
- **Indexes on (session_id, parent_id)** for folder navigation
- **UUID for sessions** allows public identifier without exposing auto-increment ID

---

## Security Design Decisions

### 1. Pod Isolation over Shared Container

**Decision:** One Kubernetes pod per active user session instead of running all user code in a shared container with chroot/cgroups.

**Why:**
- **Kernel Isolation:** Each pod can use different kernel features without conflicts
- **Network Isolation:** Kubernetes NetworkPolicies prevent cross-user traffic
- **Resource Enforcement:** Kubernetes enforces CPU/memory limits per pod
- **Clean Slate:** Pod deletion ensures no lingering processes or files
- **Blast Radius:** Exploit in one pod doesn't affect other users

**Tradeoff:** Higher resource overhead (~256Mi memory + 200m CPU per pod) vs. shared container (~50Mi per user). For a development platform, the security benefit outweighs the cost.

---

### 2. Database Credentials in Kubernetes Secrets

**Decision:** Store sensitive data (DATABASE_URL) in Kubernetes Secrets rather than hardcoded in YAML or environment variables.

**Why:**
- **No Git Commits:** Secrets never checked into version control
- **RBAC:** Access controlled via Kubernetes permissions
- **Rotation:** Can update credentials without rebuilding containers
- **Encryption at Rest:** Secrets encrypted in etcd (if configured)
- **Best Practice:** Industry standard for secret management

**Tradeoff:** More complex deployment (must create secrets separately) vs. convenience of hardcoded values. For production, security is non-negotiable.

---

### 3. RBAC Service Account for Backend

**Decision:** Backend pods run with a dedicated service account that has minimal permissions (create/delete pods, PVCs only).

**Why:**
- **Least Privilege:** Can't access other namespaces or cluster resources
- **Audit Trail:** All K8s API calls tagged with service account
- **Defense in Depth:** If backend compromised, attacker can't delete entire cluster
- **Compliance:** Required for many security frameworks (SOC2, ISO 27001)

**Tradeoff:** More complex RBAC configuration vs. using default service account with admin permissions. The security benefit is worth the one-time setup cost.

---

## Performance Design Decisions

### 1. Aggressive HPA Scale-Up, Conservative Scale-Down

**Decision:** Scale up immediately when CPU > 70%, but wait 5 minutes before scaling down.

**Why:**
- **User Experience:** Slow backend pods cause timeouts, poor UX
- **Cost vs. Speed:** Over-provisioning for a few minutes is cheap
- **Thundering Herd:** Prevents all users hitting 2 pods simultaneously
- **Stability:** Avoids flapping (scaling up and down repeatedly)

**Tradeoff:** Slightly higher cost (pods idle for 5 min before scaling down) vs. risk of user-facing latency. For a development platform, user experience is more important than saving $0.50/day.

---

### 2. Tar Archives for File Sync

**Decision:** Use tar archives sent via kubectl exec instead of syncing files one-by-one.

**Why:**
- **Efficiency:** One kubectl exec instead of N execs for N files
- **Atomicity:** All files updated together, no partial state
- **Compression:** Tar compresses text files, reducing transfer time
- **Permissions:** Tar preserves file permissions and timestamps

**Tradeoff:** More complex code (create tar, send via stdin, extract) vs. simple copy. For workspaces with 10-100 files, tar is 5-10x faster.

---

### 3. Startup Orphan Cleanup

**Decision:** On backend startup, scan for orphaned pods from previous crashes and delete them.

**Why:**
- **Cost Control:** Prevents leaked pods from accumulating
- **Clean Slate:** Ensures backend state matches cluster state
- **Self-Healing:** Recovers automatically from crashes
- **Monitoring:** Logs orphan count for debugging

**Tradeoff:** Adds 2-5 seconds to backend startup time. Acceptable for a long-lived service that restarts rarely.

---

## Code Quality Decisions

### 1. Strict mypy Type Checking

**Decision:** Enforce 100% mypy strict mode compliance with 0 errors.

**Why:**
- **Catch Bugs Early:** Type errors caught at development time, not production
- **Self-Documenting:** Type hints show function contracts
- **Refactoring Safety:** Mypy ensures refactors don't break callers
- **IDE Support:** Better autocomplete and inline error detection

**Tradeoff:** More verbose code (type annotations everywhere) vs. faster development with no types. For a multi-developer project, type safety is worth it.

---

### 2. Ruff for Linting and Formatting

**Decision:** Use Ruff (single tool) instead of Black + Flake8 + isort.

**Why:**
- **Speed:** 10-100x faster than Black + Flake8 combined
- **One Tool:** Simpler CI/CD, fewer dependencies
- **Comprehensive:** Linting + formatting + import sorting
- **Active Development:** Modern tool with frequent updates

**Tradeoff:** Newer tool (less mature) vs. established tools. Ruff has proven stable and is rapidly becoming the Python standard.

---

### 3. Organized Models and Schemas

**Decision:** Split monolithic `postgres_models.py` and `schemas.py` into domain-specific files (`users.py`, `sessions.py`, `workspace_items.py`).

**Why:**
- **Maintainability:** Easier to find and update code
- **Encapsulation:** Each file has clear responsibility
- **Testing:** Can test models independently
- **Scalability:** Easy to add new domains (e.g., `teams.py`)

**Tradeoff:** More files to navigate vs. single file with everything. For a growing codebase, organization pays off quickly.

---

## Lessons Learned

### What Worked Well

1. **Database as Source of Truth:** Never lost user data despite multiple pod crashes and cluster resets
2. **HPA:** Handled 3x traffic spike during demo without manual intervention
3. **Background Cleanup:** Saved ~$20/month in unused pod costs
4. **Type Safety:** Caught 50+ bugs before production with mypy strict mode
5. **PVC Storage:** Users appreciate fast file operations and pip caching

### What We'd Change

1. **Larger PVCs:** 1Gi is tight for data science workloads with large datasets
2. **Custom HPA Metrics:** Scale based on WebSocket connections, not just CPU
3. **File Versioning:** Users want "undo" for file changes
4. **Session Sharing:** Multiple users want to collaborate in same workspace
5. **Startup Time:** 10-20s pod creation feels slow, need image pre-pulling

### Future Improvements

1. **Multi-Region:** Deploy in multiple regions for lower latency
2. **HTTPS:** Add Ingress with Let's Encrypt for secure WebSockets
3. **Monitoring:** Add Prometheus + Grafana for better observability
4. **Rate Limiting:** Prevent abuse from automated scripts
5. **Cost Dashboard:** Show users their resource consumption

---

## Conclusion

This architecture represents a balance between:
- **Security** (isolated pods, RBAC, secrets)
- **Performance** (autoscaling, tar sync, PVC caching)
- **Cost** (aggressive cleanup, shared infrastructure)
- **Developer Experience** (fast file operations, zero data loss)

The design is not perfect—no architecture is—but it's well-suited for a multi-user development platform serving 10-50 concurrent users. As the platform grows, we can evolve these decisions based on real usage patterns and feedback.

**Key Takeaway:** Every decision has tradeoffs. The goal is not to make perfect choices, but to make informed choices that align with your priorities (in our case: security, reliability, user experience, then cost).
