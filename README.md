# 🚀 OnboardOps

### A thoughtful start for every new joiner.

Create an onboarding request, generate a task plan, and keep a human in charge of approval—even across application restarts.

**React · TypeScript · FastAPI · LangGraph · MCP · PostgreSQL · Docker**

## 🧰 Technology stack

| Layer | Technologies | Purpose |
|---|---|---|
| Frontend | React, TypeScript, Vite, CSS | Onboarding form and development tooling |
| Backend | Python, FastAPI, Pydantic, Uvicorn | APIs, validation, and HTTP server |
| Workflows | LangGraph | Planning, approval interrupts, and resumption |
| Integrations | MCP Python SDK | Employee lookup server and client |
| Storage | PostgreSQL, Psycopg, PostgresSaver | Requests, plans, and durable workflow checkpoints |
| Vector search foundation | pgvector | Extension installed; embeddings and retrieval planned |
| Containers | Docker, Docker Compose | Backend services and isolated test environments |
| Quality checks | pytest, HTTPX, ESLint, TypeScript | API and integration tests, linting, and type checking |
| Version control | Git, GitHub | Change history and repository hosting |

## ✨ What works today

- **Request, recorded.** A React form saves onboarding details through FastAPI.
- **Plan, prepared.** Rule-based tasks for HR, IT, and hiring managers, with duplicate-plan prevention.
- **Human, in control.** Persistent approval pauses, safe decision retries, and recovery after interrupted updates.
- **Tools, connected.** MCP employee lookup feeds a LangGraph planning preview.
- **Behaviour, tested.** Unit tests and isolated PostgreSQL integration tests cover validation, concurrency, and recovery.

```text
React → FastAPI → LangGraph → PostgreSQL checkpoints
                       ↘ MCP employee directory
```

The UI currently creates requests. Plan generation and approval are available through the API docs. Employee-based previews are not saved automatically.

## 🏁 Get running

You’ll need Git, a Vite-compatible Node.js installation, and Docker Desktop running Linux containers. Commands below use PowerShell.

```powershell
git clone https://github.com/gautamikh/OnBoardOps.git
cd OnBoardOps
Copy-Item .env.example .env
```

Set a local database password in `.env`; keep it out of Git. Then start the backend:

```powershell
docker compose build api
docker compose up -d
docker compose ps
```

Wait for `db` to become healthy. Initialize the tables and workflow storage:

```powershell
docker compose cp database/001_onboarding_requests.sql db:/tmp/001_onboarding_requests.sql
docker compose exec db psql -U onboardops -d onboardops -v ON_ERROR_STOP=1 -f /tmp/001_onboarding_requests.sql
docker compose cp database/002_onboarding_plans.sql db:/tmp/002_onboarding_plans.sql
docker compose exec db psql -U onboardops -d onboardops -v ON_ERROR_STOP=1 -f /tmp/002_onboarding_plans.sql
docker compose exec api python -m app.checkpoints
```

These commands use the example database and username, `onboardops`. pgvector is enabled on first database initialization.

Start the frontend in another terminal, from the project root:

```powershell
cd frontend
npm ci
npm run dev
```

**[Open the app](http://localhost:5173) · [Explore the API](http://localhost:8000/docs) · [Check readiness](http://localhost:8000/ready)**

## 🎬 Try the flow

1. Submit fictional employee details in the React form and copy the **request ID**.
2. In `/docs`, call `POST /onboarding-requests/{request_id}/plan` and copy the **plan ID**.
3. Call `POST /plans/{plan_id}/review` to pause for approval.
4. Call `POST /plans/{plan_id}/decision` with `{"decision": "approve"}` or `{"decision": "reject"}`.

For an MCP-powered preview, try `POST /plans/from-employee` with employee ID `EMP-001`, a job title, and a start date. Approval records a decision; it does not execute tasks.

## 🧪 Check your changes

From the project root, run the full backend suite against a disposable test database:

```powershell
docker compose build api
docker build -f backend/Dockerfile.test -t onboardops-tests:dev ./backend
docker compose -p onboardops-integration -f compose.test.yaml up --abort-on-container-exit --exit-code-from tests
docker compose -p onboardops-integration -f compose.test.yaml logs tests
docker compose -p onboardops-integration -f compose.test.yaml down
```

Check the live MCP connection separately:

```powershell
docker compose exec api python -m app.mcp_check
```

From `frontend`, run `npm run build` and `npm run lint`. Tests simulate MCP lookup where needed; the live check verifies the actual server connection.

## 🔭 Up next

Plan and approval screens · authenticated reviewers · policy retrieval with pgvector · LLM-generated plans · approved task execution through MCP.

**Status:** Local portfolio prototype using fictional data and deterministic planning rules. Authentication, vector retrieval, and LLM calls are not implemented yet. No AI API key is currently required.

To stop the backend, run `docker compose down`. Avoid `-v` unless you intend to delete its database volume.
