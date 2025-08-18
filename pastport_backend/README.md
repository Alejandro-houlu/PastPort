# PastPort Data Processor - FastAPI Backend

A modern FastAPI backend for the PastPort data processing application with SQLAlchemy 2.0 (async) and Alembic for database migrations.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy 2.0**: Async ORM for database operations
- **Alembic**: Database migration management
- **MySQL**: Database with SSL support
- **Environment-based Configuration**: Separate configs for development and production
- **CORS Support**: Configured for Angular frontend integration

## Project Structure

```
pastport_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py              # Configuration management
│   ├── database.py            # SQLAlchemy async setup
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic models
│   ├── api/                   # API routes
│   │   └── health.py          # Health check endpoints
│   ├── services/              # Business logic
│   ├── repositories/          # Data access layer
│   └── utils/                 # Utilities
├── alembic/                   # Database migrations
├── .env.dev                   # Development environment
├── .env.prod                  # Production environment
├── requirements.txt           # Python dependencies
├── run.py                     # Application runner
└── README.md                  # This file
```

## Setup

### 1. Install Dependencies

```bash
conda activate pastport
pip3 install -r requirements.txt
```

### 2. Environment Configuration

Copy and configure the appropriate environment file:

**For Development:**
```bash
cp .env.dev .env
```

**For Production:**
```bash
cp .env.prod .env
```

Update the `.env` file with your actual database password and other settings:
```env
DB_PASSWORD=your_actual_database_password
SECRET_KEY=your_secret_key_here
```

### 3. Database Setup

The application is configured to connect to your MySQL database:
- Host: `db-mysql-sgp1-26714-do-user-24607136-0.k.db.ondigitalocean.com`
- Port: `25060`
- Database: `pastport`
- User: `pp_admin`
- SSL: Required

## Running the Application

### Development Mode

```bash
# Run in development mode (default)
python run.py

# Or explicitly specify development
python run.py dev
python run.py development
```

The server will start on `http://localhost:8000` with:
- Auto-reload enabled
- Debug mode on
- CORS configured for Angular localhost (`http://localhost:4200`)

### Production Mode

```bash
# Run in production mode
python run.py prod
python run.py production
```

The server will start with:
- Auto-reload disabled
- Debug mode off
- CORS configured for production domains
- Optimized logging

## API Endpoints

### Health Checks

- `GET /` - Root endpoint with basic info
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/db` - Database connectivity check

### API Documentation

Once the server is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Database Migrations

### Initialize Alembic (Already Done)

```bash
alembic init alembic
```

### Create a Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Migration History

```bash
alembic history
```

## Development

### Adding New Models

1. Create model in `app/models/`
2. Import in `app/models/__init__.py`
3. Create migration: `alembic revision --autogenerate -m "Add new model"`
4. Apply migration: `alembic upgrade head`

### Adding New API Endpoints

1. Create router in `app/api/`
2. Add router to `app/main.py`
3. Create corresponding schemas in `app/schemas/`

### Environment Variables

The application supports different configurations for development and production:

**Development (.env.dev):**
- Debug mode enabled
- CORS allows localhost:4200
- Detailed logging

**Production (.env.prod):**
- Debug mode disabled
- CORS configured for production domains
- Optimized logging

## Testing the Setup

1. Start the server:
   ```bash
   python run.py
   ```

2. Test basic health check:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. Test database connectivity:
   ```bash
   curl http://localhost:8000/api/v1/health/db
   ```

4. Access API documentation:
   - Open `http://localhost:8000/docs` in your browser

## Next Steps

1. **Configure Database Password**: Update the `.env` file with your actual database password
2. **Create Models**: Add your SQLAlchemy models in `app/models/`
3. **Add API Endpoints**: Create your API routes in `app/api/`
4. **Set up Authentication**: Implement JWT authentication if needed
5. **Add Business Logic**: Implement services and repositories

## Troubleshooting

### Database Connection Issues

1. Verify database credentials in `.env` file
2. Check network connectivity to the database host
3. Ensure SSL certificates are properly configured
4. Test database connectivity using the health check endpoint

### Import Errors

1. Ensure you're in the correct conda environment: `conda activate pastport`
2. Verify all dependencies are installed: `pip3 install -r requirements.txt`
3. Check that all `__init__.py` files are present in directories

### CORS Issues

1. Verify CORS origins in your environment file
2. Ensure the Angular frontend URL is included in `CORS_ORIGINS`
3. Check that the CORS middleware is properly configured in `main.py`
