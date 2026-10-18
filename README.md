# 🚀 OnboardOps

### An AI-assisted employee onboarding coordinator

Turn onboarding requests into draft task plans across HR, IT, and hiring managers, then review those plans through a persistent approval workflow.

**Python · FastAPI · LangGraph · MCP · PostgreSQL · pgvector · Docker**

---

## 🎯 Project objective

Build an internal application that retrieves company policies, drafts grounded onboarding plans, requests human approval, and executes approved tasks through MCP integrations.

The current application uses fictional employee data and deterministic planning rules. LLM generation, policy retrieval, and task execution are future milestones.

## ✨ Implemented features

- Create, validate, and retrieve onboarding requests.
- Generate and persist one draft plan per request; repeated generation returns the existing plan.
- Pause reviews with LangGraph interrupts and resume using PostgreSQL checkpoints.
- Approve or reject saved plans; repeated matching decisions are safe and conflicting final decisions return HTTP 409.
- Recover the saved plan status on retry if the checkpoint decision was saved before an interrupted plan update.
- Discover and call a read-only MCP employee lookup tool in a separate Docker container.
- Generate employee-based previews through a LangGraph node that calls MCP.
- Check API health and database readiness.
- Run unit and isolated PostgreSQL integration tests.

## 🧰 Technology stack

| Technology | Current role |
|---|---|
| Python & FastAPI | APIs, input validation, and application logic |
| LangGraph | Planning and persistent approval workflows |
| MCP Python SDK | Employee lookup server and Python client |
| PostgreSQL | Requests, saved plans, and workflow checkpoints |
| pgvector | Installed extension; embedding ingestion and search are planned |
| Docker Compose | API, database, and MCP service orchestration |
| pytest & HTTPX | API, workflow, and database integration tests |
| React & TypeScript | Planned review interface |

## 🔄 Current workflows

```text
Saved-plan flow
Request → Validate → Save → Generate saved plan → Start review
                                                    ↓
                                        Pause in PostgreSQL
                                                    ↓
                                         Approve or reject

Employee preview flow
Employee ID + job title + start date
    → LangGraph → MCP lookup → Validate employee details → Draft preview
```

Previews are not saved automatically. Saved plans and MCP-based previews are currently separate paths. Plans use demonstration rules and calendar-day offsets; no onboarding tasks are executed.

## 🏁 Run locally

Prerequisites: Git and Docker Desktop running Linux containers. The commands below use PowerShell from the project root.

### 1. Clone the repository

```powershell
git clone https://github.com/gautamikh/OnBoardOps.git
cd OnBoardOps
```

### 2. Configure the environment

On first setup:

```powershell
Copy-Item .env.example .env
```

Set your local database password in `.env`. Do not commit this file or overwrite an existing configuration unnecessarily. Database credentials initialize a new volume; changing `.env` later does not change an existing database password.

### 3. Build and start services

The API and MCP service share an image, so build it before starting services:

```powershell
docker compose build api
docker compose up -d
docker compose ps
```

Wait for `db` to become healthy and check that `api` and `mcp-tools` are running. Inspect MCP startup with:

```powershell
docker compose logs mcp-tools
```

The API connects to PostgreSQL at `db:5432` and MCP at `http://mcp-tools:8001/mcp` on the Compose network. Only the API is published to the host, at `127.0.0.1:8000`.

### 4. Apply the database schemas

Run in this order:

```powershell
docker compose cp database/001_onboarding_requests.sql db:/tmp/001_onboarding_requests.sql
docker compose exec db psql -U onboardops -d onboardops -v ON_ERROR_STOP=1 -f /tmp/001_onboarding_requests.sql
docker compose cp database/002_onboarding_plans.sql db:/tmp/002_onboarding_plans.sql
docker compose exec db psql -U onboardops -d onboardops -v ON_ERROR_STOP=1 -f /tmp/002_onboarding_plans.sql
```

These commands assume the example database name and username, `onboardops`. Adjust them if your configuration differs. The pgvector initialization script runs automatically only when the database data directory is first initialized.

### 5. Initialize workflow checkpoints

```powershell
docker compose exec api python -m app.checkpoints
```

Expected message: `LangGraph checkpoint storage is ready.` This command can be rerun. Approval workflows use these tables to retain state across process and container restarts.

### 6. Verify MCP connectivity

```powershell
docker compose exec api python -m app.mcp_check
```

The check discovers `lookup_employee`, retrieves a known employee, checks an unknown ID, and verifies rejection of invalid input. Expected final message: `MCP connection checks passed.`

### 7. Open the API

- 📖 [Interactive API documentation](http://localhost:8000/docs)
- 💚 [API health](http://localhost:8000/health)
- 🔌 [Database readiness](http://localhost:8000/ready)

## 📡 API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API availability |
| GET | `/ready` | Check database connectivity |
| POST | `/onboarding-requests` | Create a request |
| GET | `/onboarding-requests/{request_id}` | Retrieve a request |
| POST | `/onboarding-requests/{request_id}/plan` | Generate or return the saved plan |
| GET | `/onboarding-requests/{request_id}/plan` | Retrieve the saved plan |
| POST | `/plans/preview` | Preview a plan from complete details |
| POST | `/plans/from-employee` | Preview a plan using MCP employee lookup |
| POST | `/plans/{plan_id}/review` | Start or recover a review |
| POST | `/plans/{plan_id}/decision` | Approve or reject a reviewed plan |

### 👤 Preview from an employee ID

Submit to `POST /plans/from-employee`:

```json
{
  "employee_id": "EMP-001",
  "job_title": "Backend Engineer",
  "start_date": "2026-11-02"
}
```

The fictional directory contains `EMP-001` (Maya Example) and `EMP-002` (Alex Example). An unknown employee returns 404; a directory failure returns 503. The response includes employee details and three draft tasks.

### ✅ Create and approve a saved plan

1. In `/docs`, execute `POST /onboarding-requests` with the example below.
2. Copy the response `id` as the **request ID**.
3. Execute `POST /onboarding-requests/{request_id}/plan` with that request ID.
4. Copy the plan response `id` as the **plan ID**.
5. Execute `POST /plans/{plan_id}/review` with the plan ID.
6. Expect `workflow_status: awaiting_approval` and `waiting_for_approval: true`.
7. Execute `POST /plans/{plan_id}/decision` with `{"decision": "approve"}` or `{"decision": "reject"}`.
8. Retrieve the saved plan using the **request ID** to verify its final status.

```json
{
  "employee_name": "Maya Example",
  "job_title": "Backend Engineer",
  "department": "Engineering",
  "location": "Berlin",
  "start_date": "2026-11-02"
}
```

The first plan-generation call returns 201; repeated calls return 200 with the same plan. While review is pending, the saved plan remains `draft`. Repeating a final decision returns 200; submitting the opposite decision returns 409. Approval does not execute tasks.

## 🧪 Run tests

### Build test images

```powershell
docker compose build api
docker build -f backend/Dockerfile.test -t onboardops-tests:dev ./backend
```

### Unit and workflow tests

```powershell
docker run --rm onboardops-tests:dev
```

Database integration tests are skipped in this mode. API database access and employee lookup are mocked where required.

### Full suite with isolated PostgreSQL

```powershell
docker compose -p onboardops-integration -f compose.test.yaml up --abort-on-container-exit --exit-code-from tests
docker compose -p onboardops-integration -f compose.test.yaml logs tests
```

The test project initializes a separate temporary database and does not use the development volume. Coverage includes saved plans, duplicate prevention, approval retries, conflicting concurrent decisions, and recovery from an injected failure before the plan update commits.

After inspecting the summary, clean up:

```powershell
docker compose -p onboardops-integration -f compose.test.yaml down
```

`Aborting on container exit...` is expected when tests finish. Check the pytest summary and test container exit code. These tests do not replace the live MCP connection check above or a manual container-restart persistence check.

## 🐳 Useful Docker commands

```powershell
# View service status and logs
docker compose ps
docker compose logs api
docker compose logs db
docker compose logs mcp-tools

# Restart the API to check that pending reviews survive
docker compose restart api

# Simulate and recover from an MCP outage
docker compose stop mcp-tools
docker compose start mcp-tools

# Stop development services while retaining database data
docker compose down
```

Adding `-v` to the development `down` command deletes the named database volume. Keep it out of normal shutdown commands.

## 🗺️ Next milestones

- [ ] Connect employee-based planning to persistent requests and plans
- [ ] Add authenticated reviewers, permissions, and an approval audit trail
- [ ] Add plan revisions and explicit review of changed content
- [ ] Ingest policies, generate embeddings, and retrieve sources with pgvector
- [ ] Add LLM-generated, policy-grounded plans and quality evaluations
- [ ] Execute approved tasks through MCP with duplicate prevention
- [ ] Build the React review interface
- [ ] Pin dependencies and add CI/CD, deployment, and operational monitoring

## 📌 Project status

An actively developed local portfolio prototype using fictional employee data. Authentication and reviewer authorization are not implemented. Approval decisions are persisted, but real onboarding actions are not executed. No LLM or embedding API is required for the current workflows.
