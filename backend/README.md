# Video Editor Backend

This is the backend service for the Video Editor application, built with FastAPI, SQLAlchemy, and PostgreSQL/SQLite.

## Features

- User authentication with JWT tokens
- Project management
- Video upload and processing
- Video segment management
- RESTful API with OpenAPI documentation

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- SQLite (for development) or PostgreSQL (for production)
- (Optional) Redis (for background tasks)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the `backend` directory with the following variables:
   ```env
   # App settings
   ENV=development
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
   
   # Database
   DATABASE_URL=sqlite:///./sql_app.db  # For SQLite
   # DATABASE_URL=postgresql://user:password@localhost:5432/video_editor  # For PostgreSQL
   
   # File storage
   UPLOAD_DIR=./uploads
   STATIC_DIR=./static
   MAX_UPLOAD_SIZE=104857600  # 100MB
   
   # CORS (comma-separated origins)
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   ```

5. **Initialize the database**
   ```bash
   python -m app.database
   ```

## Running the Application

### Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Production

For production, use a production-grade ASGI server like Uvicorn with Gunicorn:

```bash
pip install gunicorn

gunicorn -k uvicorn.workers.UvicornWorker -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## API Documentation

- **OpenAPI JSON**: `/api/openapi.json`
- **Interactive API docs (Swagger UI)**: `/api/docs`
- **Alternative API docs (ReDoc)**: `/api/redoc`

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── api_v1/
│   │   │   ├── __init__.py
│   │   │   └── api.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── projects.py
│   │       └── videos.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── models.py
│   ├── schemas.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── .env
├── requirements.txt
└── README.md
```

## Testing

To run tests:

```bash
pytest
```

## Deployment

For production deployment, consider using:

1. **Docker** with Docker Compose
2. **Kubernetes**
3. **Platform as a Service** like Heroku, AWS Elastic Beanstalk, or Google App Engine

## License

[MIT](LICENSE)
