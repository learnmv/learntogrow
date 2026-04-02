# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LearnToGrow is an AI-powered educational question generation platform built around California Common Core curriculum standards. It consists of a FastAPI backend (Python) and a React frontend (TypeScript + Vite).

## Architecture

### Backend (FastAPI)

Layer-based architecture in `backend/app/`:
- **Routers** (`routers/`) - HTTP request handling, route definitions
- **Services** (`services/`) - Business logic, Ollama LLM integration for question generation
- **Models** (`models/`) - SQLAlchemy ORM models for curriculum hierarchy (subjects → grades → domains → clusters → standards)
- **Schemas** (`schemas/`) - Pydantic request/response validation

Key endpoints under `/api/v1`: `/subjects`, `/grades`, `/domains`, `/clusters`, `/standards`, `/questions/generate`

The backend connects to PostgreSQL for curriculum data and Ollama (local LLM) for question generation. Configuration via `backend/.env` or environment variables.

### Frontend (React + TypeScript + Vite)

Standard Vite React project in `frontend/`:
- **Entry**: `src/main.tsx` → `src/App.tsx`
- **Components** (`components/`) - React components including `Quiz.tsx` and `ui/` subcomponents
- **Services** (`services/`) - API client utilities (`api.ts` fetch wrapper, `standards.ts` curriculum API, `questions.ts` generation API)
- **Types** (`types/`) - TypeScript interfaces matching backend schemas

Styling uses Tailwind CSS 4 with custom color palette (sage, coral, sand) defined in `src/index.css`.

## Development Commands

### Frontend

```bash
cd frontend
npm install
npm run dev          # Start dev server (Vite)
npm run build        # Type check + build for production
npm run lint         # ESLint
npm run preview      # Preview production build
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend auto-reloads on file changes. API docs available at `http://localhost:8000/docs` (Swagger) and `/redoc`.

### Database

The PostgreSQL schema is defined in `schema.sql` at the repository root. Tables: `subjects`, `grades`, `domains`, `clusters`, `standards`.

## CI/CD

GitHub Actions workflows use a self-hosted runner:
- **Dev** (`.github/workflows/dev.yml`): Builds images on push to `dev` branch, saves to `/home/sysadmin/dev-builds/`
- **Prod** (`.github/workflows/prod.yml`): Builds images on push to `main`, saves to `/home/sysadmin/prod-builds/`, creates GitHub release

Kubernetes manifests in `k8s/`:
- Deployments use `imagePullPolicy: Never` for local images
- Requires `k8s/secrets.yaml` (gitignored) for database credentials
- Ingress configured for `learntogrow.local`

## Important File Locations

- Backend config: `backend/app/config.py` (Pydantic settings, reads from `.env`)
- Frontend API base URL: `frontend/src/lib/constants.ts` (`VITE_API_URL` env var)
- Database connection: `backend/app/database.py`
- Question generation logic: `backend/app/services/questions.py`
- Ollama integration: Configured via `OLLAMA_URL` and `OLLAMA_MODEL` env vars

## Code Patterns

### Adding a Backend Endpoint

1. Add service method in `app/services/curriculum.py` (or appropriate service)
2. Add route in `app/routers/<entity>.py`
3. Update `app/schemas/<entity>.py` if response model changes
4. Register router in `app/main.py` with `app.include_router()`

### Frontend API Calls

Use the typed service functions in `frontend/src/services/`:
```typescript
import { fetchSubjects } from './services/standards'
const subjects = await fetchSubjects()
```

The `fetchApi` wrapper in `api.ts` handles JSON parsing and error throwing for non-OK responses.

## External Dependencies

- **PostgreSQL**: External database at `192.168.191.213:5432` (configurable)
- **Ollama**: Expected at `http://localhost:11434` (or `http://host.docker.internal:11434` in containers)
- **Kubernetes**: Self-hosted cluster with nginx-ingress controller
