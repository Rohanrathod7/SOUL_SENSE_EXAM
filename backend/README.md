# FastAPI Backend - Soul Sense EQ Test

A comprehensive REST API for the Soul Sense Emotional Intelligence Assessment Platform.

## 🚀 Quick Start

```bash
# 1. Install dependencies
cd backend/fastapi
pip install -r requirements.txt

# 2. Ensure main app database is set up
cd ../..
python -m scripts.setup_dev

# 3. Start the backend server
cd backend/fastapi
python start_server.py
```

The API will be available at:

- **API**: http://127.0.0.1:8000
- **Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📋 Available Routers

| Router          | Prefix              | Description                                                       |
| --------------- | ------------------- | ----------------------------------------------------------------- |
| **health**      | `/`                 | Health checks and API status                                      |
| **auth**        | `/auth`             | User registration and JWT authentication                          |
| **users**       | `/api/users`        | User management (CRUD)                                            |
| **profiles**    | `/api/profiles`     | User profiles (settings, medical, personal, strengths, emotional) |
| **assessments** | `/api/assessments`  | Assessment management and statistics                              |
| **questions**   | `/api/questions`    | Question bank and categories                                      |
| **analytics**   | `/api/v1/analytics` | Analytics, trends, and benchmarks                                 |
| **journal**     | `/api/v1/journal`   | Journal entries, analytics, and prompts                           |

## 🏗️ Architecture

```
backend/fastapi/
├── api/                     # Core API Logic (Renamed from app to avoid collisions)
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Environment configuration
│   ├── routers/             # API endpoints
│   ├── models/              # Pydantic schemas (Request/Response)
│   └── services/            # Business & Database logic
├── tests/                   # Test Suite
├── scripts/                 # Developer & OPS Scripts
├── start_server.py          # Unified Server startup script
└── requirements.txt         # Dependencies
```

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Login Example

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

## 📊 Database

The backend shares the SQLite database with the main desktop application:

- **Location**: `SOUL_SENSE_EXAM/data/soulsense.db`
- **Models**: Business entities are imported from the root `app/models.py`.

## 🤝 Contributing

When adding new features to the backend:

1. **Internal Imports**: Use relative imports within the `api` package (e.g., `from ..services import ...`).
2. **Naming**: Do **not** use `app` as a package name inside the backend to avoid conflicts with the root application.
3. **Docs**: Ensure new endpoints are documented via Swagger (`/docs`).

---

**Built with FastAPI** | **Part of Soul Sense EQ Platform**
