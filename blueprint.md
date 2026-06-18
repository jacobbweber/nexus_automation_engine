## TL;DR

This specification defines the architecture, data schemas, and API contracts for a unified, vendor-agnostic Automation Control Plane (codename: **Nexus Automation Engine**). It provides an enterprise-grade React/Vite/Tailwind front end and a Python FastAPI backend engineered to abstract, secure, and orchestrate underlying platforms (Ansible AAP, Terraform, PowerShell/Python executors) while integrating natively with ServiceNow, CyberArk, and Dynatrace.

---

## 1. System Engineering Prompt for Autonomous Developer Agent

```text
You are an expert autonomous principal software engineer and platform architect. Your task is to implement a complete, production-grade, functional Proof of Concept (POC) for the "Nexus Automation Control Plane." This platform acts as a unified, vendor-agnostic front-end interface and orchestrator that abstracts backend automation systems (Ansible Automation Controller/AAP, Terraform, and Jump-box execution scripts) into a single, highly secure, enterprise-grade surface layer.

The implementation must be fully functional, self-contained, containerized via Docker for local execution, and architected for deployment onto Red Hat OpenShift. Do not use placeholders, stubs, or mock implementations that lack underlying state logic; utilize local in-memory databases, file-based storage, or simulated loopback interfaces that accurately mimic real-world network and API behaviors (including streaming logs, state transitions, and RBAC enforcement).

Follow the precise architectural boundaries, directory structures, database schemas, and API contracts defined below.

```

---

## 2. Architectural Design & System Topography

### Execution Architecture

```
                   +---------------------------------------+
                   |       React / Vite / Tailwind UI      |
                   +---------------------------------------+
                                       |
                                       | REST / WebSockets (TLS 1.3)
                                       v
                   +---------------------------------------+
                   |        FastAPI Core Application       |
                   +---------------------------------------+
                    /                  |                  \
                   /                   |                   \
                  v                    v                    v
      +-----------------------+ +--------------+ +------------------------+
      |  Ansible AAP Adapter  | |  IaC Engine  | | Execution Agent Hub    |
      |   (REST API Client)   | | (Terraform)  | | (SSH / WinRM / Py)   |
      +-----------------------+ +--------------+ +------------------------+
                  |                    |                    |
                  v                    v                    v
      +-----------------------+ +--------------+ +------------------------+
      | Ansible Tower / AAP   | | Terraform OSS| | Windows/Linux Jumpbox |
      | Jobs/Workflows/Scales | | / Enterprise | | PowerShell Core / Bash |
      +-----------------------+ +--------------+ +------------------------+

```

### Component Isolation Strategy

* **Frontend Surface Layer:** React 18+, Vite, Tailwind CSS, TypeScript. Strict separation between presentation components and state/API hook layers. Employs a cohesive corporate-dark/light visual hierarchy using high-contrast slate configurations.
* **Backend Application Server:** Python 3.11+ using FastAPI. Built asynchronous-first (`async/await`) utilizing `Uvicorn` as the ASGI web server.
* **Data & State Management:** SQLAlchemy 2.0 ORM with a local SQLite file database for container state persistence.
* **Job Execution & Telemetry Engine:** Background workers powered by Python `asyncio` queues to simulate/proxy live executions, managing stdout/stderr stream captures asynchronously via WebSockets.

---

## 3. Technology Stack & Directory Structure

### Stack Definition

* **Frontend:** React, Vite, Tailwind CSS, Lucide React (Icons), Radix UI (Primitives/Accessibility), Axios / Native Reconnecting WebSockets.
* **Backend:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, PyJWT (Authentication & RBAC), AsyncSSH / Paramiko (Jump-box integrations), HTTPX (Async HTTP client for third-party systems).
* **Containerization:** Multi-stage `Dockerfile` minimizing footprint and ensuring rootless execution suitable for OpenShift Security Context Constraints (SCC).

### Directory Blueprint

```text
nexus-control-plane/
├── .github/workflows/ci-cd.yaml
├── docker-compose.yaml
├── Dockerfile
├── README.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/            # SQLAlchemy Database Models
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── jobs.py
│   │   │   └── integrations.py
│   │   ├── schemas/           # Pydantic Validation Schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── jobs.py
│   │   │   └── integrations.py
│   │   ├── api/               # API Routes (V1)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── jobs.py
│   │   │   └── integrations.py
│   │   ├── core/              # RBAC Middleware & Security
│   │   │   ├── rbac.py
│   │   │   └── security.py
│   │   └── services/          # Automation Driver Adaptors
│   │       ├── ansible.py
│   │       ├── terraform.py
│   │       ├── cyberark.py
│   │       ├── servicenow.py
│   │       └── script_executor.py
│   ├── requirements.txt
│   └── run.sh
└── frontend/
    ├── index.html
    ├── package.json
    ├── tailwind.config.js
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── components/        # Reusable UI Architecture
        │   ├── common/
        │   ├── layout/
        │   └── widgets/
        ├── context/           # Auth and Global State
        ├── hooks/            # Custom API / Stream hooks
        ├── pages/             # Layout Blueprints
        │   ├── Dashboard.tsx
        │   ├── Catalog.tsx
        │   ├── JobConsole.tsx
        │   └── Settings.tsx
        └── services/          # API Client Layer

```

---

## 4. Database Schema & Data Models

The local relational storage engine must track entities to enforce RBAC permissions and handle state management across distinct automation engines.

```text
+---------------------------------------------------------------------------------+
|                                 RBAC & ORG ENTITIES                             |
+---------------------------------------------------------------------------------+
|  [Organization] 1 ---- * [Team] 1 ---- * [UserTeam] * ---- 1 [User]             |
|  [Organization] 1 ---- * [AssetGroup] 1 ---- * [ResourcePermission]             |
+---------------------------------------------------------------------------------+
|                               AUTOMATION INVENTORIES                            |
+---------------------------------------------------------------------------------+
|  [AssetGroup] 1 ---- * [TargetAsset] (Servers/Inventories)                       |
|  [AutomationJob] * ---- 1 [AssetGroup]                                          |
|  [AutomationJob] * ---- 1 [User] (Auditable Executor)                           |
|  [JobLogStream] * ---- 1 [AutomationJob]                                        |
+---------------------------------------------------------------------------------+

```

### 1. User & Authentication Models

```python
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True) # UUID
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    global_role = Column(String, default="operator") # admin, engineer, operator, consumer

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

class Team(Base):
    __tablename__ = "teams"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

```

### 2. Resource & Permission Models

```python
class AssetGroup(Base):
    __tablename__ = "asset_groups"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g., "Windows Production Jumpboxes"
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

class ResourcePermission(Base):
    __tablename__ = "resource_permissions"
    id = Column(String, primary_key=True, index=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    resource_type = Column(String, nullable=False) # "ansible_template", "terraform_config", "script"
    resource_id = Column(String, nullable=False)   # External or Internal UUID
    permission_level = Column(String, nullable=False) # "execute", "read", "write", "admin"

```

### 3. Automation & Execution Telemetry Models

```python
class AutomationJob(Base):
    __tablename__ = "automation_jobs"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    engine_type = Column(String, nullable=False) # "ansible", "terraform", "powershell_script"
    status = Column(String, default="PENDING")   # PENDING, RUNNING, SUCCESS, FAILED, CANCELED
    initiated_by = Column(String, ForeignKey("users.id"), nullable=False)
    asset_group_id = Column(String, ForeignKey("asset_groups.id"), nullable=True)
    execution_parameters = Column(Text, nullable=False) # JSON-serialized map of inputs/surveys
    backend_reference_id = Column(String, nullable=True) # AAP Job ID or Terraform Run ID
    check_mode = Column(Boolean, default=False)
    diff_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

class JobLogStream(Base):
    __tablename__ = "job_log_streams"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("automation_jobs.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    stream_type = Column(String, default="stdout") # stdout, stderr, system
    message = Column(Text, nullable=False)

```

---

## 5. Backend REST & WebSocket API Contracts

### Authentication Endpoints

* **`POST /api/v1/auth/login`**
* **Payload:** `{"username": "...", "password": "..."}`
* **Response:** `{"access_token": "...", "token_type": "bearer", "user": {"id": "...", "global_role": "..."}}`



### Job Control Plane Endpoints

* **`GET /api/v1/jobs/templates`**
* Fetches available unified runner definitions filtered by user access profile.
* **Response Schema:**
```json
[
  {
    "id": "tpl_ansible_patching_01",
    "name": "Enterprise OS Security Patching Workflow",
    "engine_type": "ansible",
    "description": "Applies rolling security patches across Linux/Windows compute structures.",
    "markdown_documentation": "# Security Patching Workflow\n\nThis template executes patching via Ansible AAP.\n\n### Execution Guardrails:\n* **Check Mode Supported:** Yes\n* **Dynamic Inventories Required:** ServiceNow CMDB Picker mapping.",
    "supports_check_mode": true,
    "supports_diff_mode": true,
    "survey_fields": [
      {
        "field_name": "target_env",
        "type": "select",
        "choices": ["Development", "Staging", "Production"],
        "required": true
      }
    ]
  }
]

```




* **`POST /api/v1/jobs/execute`**
* Dispatches an automation blueprint.
* **Payload Schema:**
```json
{
  "template_id": "tpl_ansible_patching_01",
  "check_mode": false,
  "diff_mode": true,
  "variables": {
    "target_env": "Production",
    "servicenow_ritm": "RITM0987123"
  }
}

```


* **Response:** `{"job_id": "job_uuid_12345", "status": "PENDING"}`



### Log Telemetry WebSocket Contract

* **`WS /api/v1/jobs/{job_id}/stream`**
* Connection upgrades to WebSocket and pushes records continuously as the background worker appends events.
* **Output Frame Format:**
```json
{
  "timestamp": "2026-06-18T13:40:08.001Z",
  "stream_type": "stdout",
  "message": "PLAY [Web Servers Production Configuration Run] ******************************"
}

```





---

## 6. Integration Connectors Specification

To fulfill the requirements of native execution or metadata extraction, the application server exposes abstraction adapters.

```text
+-----------------------------------------------------------------------------------+
|                            EXTERNAL CONNECTOR SERVICES                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +-------------------+      +------------------+      +-----------------------+   |
|  |    CyberArk Provider |      | ServiceNow CMDB  |      |   Dynatrace Telemetry |   |
|  +-------------------+      +------------------+      +-----------------------+   |
|  | Intercepts variables |      | Injects dynamic  |      | Decorates job records |   |
|  | fetching temporary   |      | infrastructure   |      | with system events    |   |
|  | secrets safely.      |      | pickers into UI. |      | for context logs.     |   |
|  +-------------------+      +------------------+      +-----------------------+   |
|                                                                                   |
+-----------------------------------------------------------------------------------+

```

### CyberArk Provider Integration

* Intercepts execution variables before target dispatching.
* If a parameter defines an environment target credential reference, the worker queries the CyberArk API to lease safe credentials (`/AIMWebService/api/Accounts`).
* Secrets exist only within memory during execution space lifetimes; they are never persisted to databases or written to standard logs.

### ServiceNow CMDB & Request (RITM) Bridge

* **Dynamic Target Asset Picker:** The interface populates selection scopes by reading ServiceNow tables (`/api/now/table/cmdb_ci_server`).
* **Execution Validation:** Before running configurations against production environments, the engine validates that the provided `servicenow_ritm` matches an approved state via `/api/now/table/sc_req_item`.

### Dynatrace Telemetry Sync

* Provides a parallel monitoring dashboard context pane inside the log execution console view.
* When a job initiates, the controller fetches active platform event logs (`/api/v2/events`) or metric bounds relating to target nodes from Dynatrace, embedding live environment failure alerts adjacent to structural execution log events.

---

## 7. Granular RBAC & Permission Matrix Blueprint

The authorization validation system overrides global permissions by tracing matching nodes down hierarchical chains: Organization $\rightarrow$ Team $\rightarrow$ AssetGroup Access.

| Global Role | View Jobs | Create Templates | Execute Check Mode | Execute Live Mutation | Manage Integrations |
| --- | --- | --- | --- | --- | --- |
| **Admin** | Yes | Yes | Yes | Yes | Yes |
| **Engineer** | Yes | Yes | Yes | Yes | No |
| **Operator** | Yes | No | Yes | Yes (Restricted Assets) | No |
| **Consumer** | Yes (Own) | No | Yes (Selected Assets) | No | No |

### Execution Evaluation Pipeline

```python
def verify_execution_entitlement(user_context, template_id, target_assets):
    """
    Enforces contextual authorization layers during API execution.
    """
    if user_context.global_role == "admin":
        return True
        
    # Extract asset grouping bindings
    has_explicit_allowance = db.query(ResourcePermission).filter(
        ResourcePermission.resource_id == template_id,
        ResourcePermission.resource_type == "automation_template",
        ResourcePermission.permission_level.in_(["execute", "admin"]),
        ResourcePermission.user_id == user_context.id
    ).first()
    
    if not has_explicit_allowance:
        raise HTTPException(status_code=403, detail="Deficient operational permissions for targeted workflow template.")
        
    return True

```

---

## 8. Frontend Interface Requirements (React + Tailwind)

### Visual Identity Guardrails

* **Theme Definition:** High-contrast neutral color palettes. Dark mode uses deep slates and charcoal backing elements to present clean legibility suited for long operations monitoring.
* **Layout Layout Structure:** Single frame console view tracking a primary responsive navigation pane, a fluid content viewport, and context drawers for documentation lookup.

### Page 1: Unified Service Automation Catalog

* **Core Function:** Presents cards representing unified automation templates across all execution engines.
* **UI Controls:** Filter categories by platform (Ansible, Terraform, Native Script), searchable by description tags.
* **Survey Renderer Component:** Clicking a template parses the JSON parameter schema definitions and structurally renders interactive form items (dropdown inventories mapped directly to backend ServiceNow endpoints, execution parameter toggles).

### Page 2: Advanced Telemetry Console & Execution Viewer

* Separate the distinct behavioral paradigms of infrastructure deployments versus software configuration state tasks by embedding explicit infrastructure design rules:

```text
+---------------------------------------------------------------------------------+
|                       EXECUTION VIEWPORT PARADIGM SPLIT                         |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  [TERRAFORM IA-CODE VIEWER]                  [ANSIBLE AAP CONFIG MANAGER]       |
|  +-------------------------------------+     +-------------------------------+  |
|  | - State Resource Tree Component     |     | - Host Target Execution Matrix|  |
|  | - Plan vs Realized Drift Inspector  |     | - Check Mode/Diff Assertions  |  |
|  | - Immutable Infrastructure Locks    |     | - Real-time Task Breakdown    |  |
|  +-------------------------------------+     +-------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+

```

* **Live Streaming Pane:** Standard out text field outputting continuous terminal strings with support for line searching and ANSI regex rendering styles.
* **Context Documentation Drawer:** Sliding interactive side element formatting raw markdown specifications derived directly from structural template definitions, helping technicians decipher parameters on demand without switching tabs.

---

## 9. Comprehensive Execution Simulation Sandbox Data

The following initial mock data states must be fully operational inside the in-memory layer of the application upon the first build iteration to demonstrate the system capabilities.

### 1. In-Memory Job Telemetry Data State

```python
INITIAL_JOBS_MOCK = [
    {
        "id": "job-sim-001",
        "name": "Provision Multi-Node OpenShift Infrastructure Cluster",
        "engine_type": "terraform",
        "status": "SUCCESS",
        "initiated_by": "user-eng-02",
        "check_mode": false,
        "diff_mode": false,
        "execution_parameters": "{\"cluster_name\": \"prod-east-01\", \"node_count\": 12}",
        "created_at": "2026-06-18T10:00:00Z",
        "started_at": "2026-06-18T10:00:05Z",
        "finished_at": "2026-06-18T10:14:22Z"
    },
    {
        "id": "job-sim-002",
        "name": "Remediate Compliance Drift: OpenSSH Server Configuration",
        "engine_type": "ansible",
        "status": "RUNNING",
        "initiated_by": "user-op-05",
        "check_mode": true,
        "diff_mode": true,
        "execution_parameters": "{\"target_tier\": \"pci-dss-hosts\"}",
        "created_at": "2026-06-18T13:38:00Z",
        "started_at": "2026-06-18T13:38:10Z",
        "finished_at": None
    }
]

```

### 2. Simulated Stream Generator Logic

```python
async def simulate_live_ansible_stream(job_id: str, queue: asyncio.Queue):
    """
    Simulates operational output events for the running Ansible job.
    """
    logs = [
        "TASK [Gathering Facts] *********************************************************",
        "ok: [linux-compute-001.enterprise.internal]",
        "ok: [linux-compute-002.enterprise.internal]",
        "TASK [Enforce Secure Protocol Compliance: SSHD Config] ************************",
        "--- before: /etc/ssh/sshd_config\n+++ after: /etc/ssh/sshd_config\n@@ -14,4 +14,4 @@\n-Protocol 1,2\n+Protocol 2",
        "changed: [linux-compute-001.enterprise.internal] (CHECK MODE)",
        "changed: [linux-compute-002.enterprise.internal] (CHECK MODE)",
        "PLAY RECAP *********************************************************************",
        "linux-compute-001.enterprise.internal : ok=2    changed=1    unreachable=0    failed=0",
        "linux-compute-002.enterprise.internal : ok=2    changed=1    unreachable=0    failed=0"
    ]
    for line in logs:
        await asyncio.sleep(1.5) # Emulate operational task processing latency
        await queue.put({"timestamp": datetime.utcnow().isoformat(), "stream_type": "stdout", "message": line})

```

---

## 10. Verification Validation Criteria

Your implementation will be declared functional and compliant only when meeting all components within this criteria checklist:

* **Zero Placer Rule:** No placeholder text files or non-functional structural views exist in the output codebase.
* **Strict Authentication Guards:** Accessing endpoints or frontend interfaces without a verified authorization header explicitly yields clean rejection messages.
* **Responsive Control Streams:** Changing the state selection context updates values dynamically, signaling operational readiness across structural elements.

To ensure this Proof of Concept (POC) is fully demonstrable and visually represents a heavily utilized enterprise environment, you must implement a "Hyper-Realistic Stateful Simulation Engine" within the FastAPI backend. The system must feel 100% alive. Every button, filter, job run, and telemetry graph must interact with a cohesive, stateful backend simulation. Do not use static mock arrays; build a dynamic state machine using a persistent local SQLite database (`sqlite:///./nexus_simulation.db`) initialized via a comprehensive seeding script on startup.

**10.1 Stateful Job Execution Lifecycle**
All job executions must follow a strict, stateful lifecycle (Pending -> Running -> Success/Failed) managed by an `asyncio` background task queue.
* When a user triggers a job (e.g., Terraform Plan or Ansible Check Mode), the API must write the record to the database and immediately return the new Job ID.
* The frontend will connect via WebSocket. The backend background worker will then stream realistic, delayed logs into the database and over the socket.
* Once the stream completes, the backend updates the job state to "SUCCESS" or "FAILED", which must dynamically reflect in the UI without requiring a page refresh.

**10.2 The "Heavily Used" Historical Seed Data**
The startup script must populate the database with a rich history to make the dashboard look like a lived-in enterprise system.
* Generate at least 50+ historical job executions spanning the last 30 days.
* Include a realistic distribution of statuses: 70% SUCCESS, 20% FAILED (with actual error logs), 10% CANCELLED.
* Distribute the historical runs across various users, teams, and target environments (Development, Staging, Production).

**10.3 Core Interactive Workflows (Terraform & Ansible)**
The simulation engine must include specific, highly detailed workflow templates that the user can execute. Implement specific log generators for the following scenarios:

* **Scenario 1: Infrastructure Provisioning (Terraform)**
    * **Name:** `Provision AWS EKS Cluster & Node Groups`
    * **Behavior:** Clicking "Plan" streams standard Terraform plan output (calculating dependencies, refreshing state, `Plan: 45 to add, 0 to change, 0 to destroy`). Clicking "Apply" streams the actual creation process with 1-3 second delays between resource creations.
* **Scenario 2: Post-Provisioning Configuration (Ansible)**
    * **Name:** `RHEL 9 CIS/STIG Compliance Enforcement`
    * **Behavior:** Clicking "Check Mode" streams yellow ANSI-colored text showing what *would* change. Clicking "Run" streams the actual state mutations. Includes gathering facts, applying SSHD configs, rotating PAM modules, etc.
* **Scenario 3: Day 2 Operations (Python/PowerShell)**
    * **Name:** `Emergency IIS Application Pool Recycle & Cache Clear`
    * **Behavior:** Fast execution, simulating a WinRM jump-box call. Shows verbose output of services stopping and starting.
* **Scenario 4: Intentional Failure (For UI Demonstration)**
    * **Name:** `ServiceNow CMDB Dynamic Sync`
    * **Behavior:** Intentionally fails at the 15-second mark, streaming a realistic HTTP 503 error or Auth token expiration log, changing the UI state to red/FAILED, and triggering a mock Dynatrace alert in the UI context pane.

**10.4 Realistic Log Generators & ANSI Support**
Do not use generic "Step 1, Step 2" logs. The backend must contain factory functions that yield actual text dumps from Terraform and Ansible runs.
* Inject ANSI escape codes (colors, bold text) into the simulated logs. The React frontend terminal component (e.g., `xterm.js` or a custom Tailwind log viewer) must parse and render these colors correctly to mimic a real operator console.
* Introduce jitter (randomized sleep times between 0.1s and 2.5s) between log lines to simulate network latency and actual compute time.

**10.5 Simulated Observability & Telemetry Context**
To fulfill the Dynatrace/telemetry integration requirement:
* The backend must expose a `/api/v1/telemetry/{job_id}` endpoint that generates a time-series array of CPU/Memory usage metrics correlated to the job's duration.
* The frontend Job Console must include a "System Telemetry" tab or side-drawer that renders these metrics using a charting library (e.g., Recharts or Chart.js), making it appear as though the user is monitoring the jump-box's performance in real-time during the run.