# LearnToGrow FastAPI Backend

FastAPI backend for accessing California Common Core curriculum standards.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic settings management
│   ├── database.py          # SQLAlchemy engine and session
│   ├── dependencies.py      # FastAPI dependency injection
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── subject.py
│   │   ├── grade.py
│   │   ├── domain.py
│   │   ├── cluster.py
│   │   └── standard.py
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── subject.py
│   │   ├── grade.py
│   │   ├── domain.py
│   │   ├── cluster.py
│   │   └── standard.py
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── curriculum.py    # Curriculum operations
│   │   └── search.py        # Search functionality
│   └── routers/             # HTTP route handlers
│       ├── __init__.py
│       ├── subjects.py
│       ├── grades.py
│       ├── domains.py
│       ├── clusters.py
│       └── standards.py
├── venv/                    # Python virtual environment
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md               # This file
```

## Architecture

This project follows a **layer-based architecture**:

| Layer | Responsibility | Flow |
|-------|----------------|------|
| **Routers** | HTTP request handling | Receive request, call service, return response |
| **Services** | Business logic | Query models, apply filters, aggregations |
| **Models** | Database schema | SQLAlchemy table definitions |
| **Schemas** | Data validation | Pydantic request/response models |

**Request Flow:** Router → Service → Model → Database

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `.env` file:

```env
DB_HOST=192.168.191.213
DB_PORT=5432
DB_NAME=learntogrow_dev
DB_USER=admin
DB_PASSWORD=admin@123
```

### 4. Run the Server

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/subjects` | List all subjects |
| GET | `/api/v1/grades` | List all grades (optional: `?subject_id=1`) |
| GET | `/api/v1/domains` | List all domains (optional: `?subject_id=1`) |
| GET | `/api/v1/clusters` | List all clusters (optional: `?domain_id=1&grade_id=1`) |
| GET | `/api/v1/standards` | List standards with filters |

### Standards Query Parameters

- `skip` - Pagination offset (default: 0)
- `limit` - Max results (default: 100, max: 1000)
- `grade_id` - Filter by grade
- `domain_id` - Filter by domain
- `cluster_id` - Filter by cluster
- `min_difficulty` - Min difficulty (0.0 - 1.0)
- `max_difficulty` - Max difficulty (0.0 - 1.0)

Example: `/api/v1/standards?grade_id=1&limit=10`

## API Documentation

Interactive documentation available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database Schema

The backend connects to a PostgreSQL database with the following tables:

- **subjects** - Top-level subjects (Math, ELA, etc.)
- **grades** - Grade levels within subjects
- **domains** - Major conceptual domains
- **clusters** - Clusters of related standards
- **standards** - Individual learning standards

See `../schema.sql` for full schema definition.

## Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

## Requirements

- Python 3.12+
- PostgreSQL 16+
- See `requirements.txt` for Python packages

## Development

### Adding New Endpoints

1. Add service method in `app/services/curriculum.py`
2. Add router endpoint in `app/routers/<entity>.py`
3. Update `app/schemas/<entity>.py` if new response model needed

### Running Tests

```bash
source venv/bin/activate
python -c "from app.main import app; print('Import OK')"
```

## License

Private - LearnToGrow Project
