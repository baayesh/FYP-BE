# Retinify LMS Backend

This is the backend API for the Retinify Learning Management System built with FastAPI.

## 🏗️ Architecture

The application follows a 3-layer architecture:

- **Presentation Layer**: FastAPI routers and endpoints (`app/api/`)
- **Business Logic Layer**: Service classes (`app/services/`)
- **Data Access Layer**: Repository classes (`app/repositories/`)

## 📁 Project Structure

```
retinify_backend/
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   ├── core/                 # Core configuration
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── repositories/        # Data access layer
│   ├── middleware/          # Custom middleware
│   └── utils/               # Utility functions
├── migrations/              # Database migrations
├── static/                  # Static files
├── requirements.txt         # Dependencies
├── main.py                 # Application entry point
└── alembic.ini            # Database migration config
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (optional, for caching)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Update `.env` with your configuration

5. Set up database:
   ```bash
   alembic upgrade head
   ```

6. Run the application:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

- Interactive API docs: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`
- OpenAPI spec: `http://localhost:8000/openapi.json`

## 🔑 Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## 🧪 Testing

Run tests with:
```bash
pytest
```

## 📦 Dependencies

Key dependencies:
- **FastAPI**: Modern web framework
- **SQLAlchemy**: ORM for database operations  
- **Alembic**: Database migrations
- **Pydantic**: Data validation
- **python-jose**: JWT token handling
- **passlib**: Password hashing
- **psycopg2**: PostgreSQL adapter

## 🔧 Configuration

Configuration is managed through environment variables. See `.env.example` for all available options.

## 📄 License

This project is licensed under the MIT License.