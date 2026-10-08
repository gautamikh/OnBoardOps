# OnboardOps

An AI-assisted employee onboarding coordinator.

Planned technologies: Python, FastAPI, LangGraph, MCP,
PostgreSQL with pgvector, and Docker Compose.

## Current functionality

- FastAPI backend with a health endpoint
- Docker image running as a non-root user
- Docker Compose configuration for local development

## Run locally

With Docker Desktop running:

```powershell
docker compose up --build -d
```

Health endpoint: http://localhost:8000/health

API documentation: http://localhost:8000/docs

## View logs

```powershell
docker compose logs api
```

## Stop

```powershell
docker compose down
```