# 🚀 OnboardOps

### An AI-assisted employee onboarding coordinator

Turn onboarding requests into structured task plans across HR, IT, and hiring managers.

Built step by step with **Python · FastAPI · LangGraph · PostgreSQL · pgvector · Docker**.

---

## 🎯 Project objective

Build an internal application that retrieves relevant company policies,
drafts onboarding plans, requests human approval, and executes approved
tasks through MCP integrations.

The current implementation supports request storage and a rule-based
LangGraph plan preview. AI generation, policy retrieval, and task execution
are upcoming milestones.


## 🧰 Technology stack

| Technology | Purpose |
|---|---|
| Python & FastAPI | Backend APIs and validation |
| PostgreSQL | Persistent application records |
| pgvector | Foundation for policy embeddings and vector search |
| LangGraph | Onboarding workflow orchestration |
| Docker Compose | Local services, networking, and storage |
| pytest & HTTPX | Automated testing |
| MCP — planned | Tool-based integrations |
| React & TypeScript — planned | Request and approval interface |

## 🔄 Current workflow

```text
Submit details → Validate → Save request → Retrieve by ID

Preview details → LangGraph validation → Draft task plan
```

Plan previews currently run separately from saved requests. They use
fictional rules and do not save or execute tasks.

## 🏁 Run locally

### 1. Clone the repository

```powershell
git clone https://github.com/gautamikh/OnBoardOps.git
cd OnBoardOps
```

### 2. Configure the environment

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Set your local database password in `.env`. Keep this file out of Git.

### 3. Start the services

With Docker Desktop running:

```powershell
docker compose up --build -d
docker compose ps
```

Wait for the database service to become healthy.

### 4. Apply the request table schema

```powershell
docker compose cp database/001_onboarding_requests.sql db:/tmp/001_onboarding_requests.sql
docker compose exec db psql -U onboardops -d onboardops -v ON_ERROR_STOP=1 -f /tmp/001_onboarding_requests.sql
```

These commands assume the example database name and username: `onboardops`.

The pgvector initialization script runs automatically when the database
volume is first created.

### 5. Explore the API

- 📖 Interactive documentation: http://localhost:8000/docs
- 💚 API health: http://localhost:8000/health
- 🔌 Database readiness: http://localhost:8000/ready

## 📡 API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API availability |
| GET | `/ready` | Check database connectivity |
| POST | `/onboarding-requests` | Create an onboarding request |
| GET | `/onboarding-requests/{request_id}` | Retrieve a saved request |
| POST | `/plans/preview` | Generate a draft task plan |

### Example request

```json
{
  "employee_name": "Maya Example",
  "job_title": "Backend Engineer",
  "department": "Engineering",
  "location": "Berlin",
  "start_date": "2026-11-02"
}
```

Use fictional employee information while developing.

## 🧪 Run tests

Build the latest application image, then build and run the test image:

```powershell
docker compose build api
docker build -f backend/Dockerfile.test -t onboardops-tests:dev ./backend
docker run --rm onboardops-tests:dev
```

Tests cover input validation, API responses, simulated database failures,
and workflow behaviour. Database access is mocked in the API tests;
this suite does not verify real SQL execution or persistence.

## 🐳 Useful Docker commands

View logs:

```powershell
docker compose logs api
docker compose logs db
```

Stop services while preserving database data:

```powershell
docker compose down
```

Avoid adding `-v` unless you intend to delete the database volume.



## 📌 Project status

Under active development as a hands-on engineering portfolio project.
The application is a local prototype and does not yet enforce user
authentication or execute real onboarding actions.