#!/usr/bin/env python3
"""
Run script for PastPort Data Processor FastAPI application

Usage:
    python run.py                    # Uses development environment
    python run.py dev                # Uses development environment
    python run.py prod               # Uses production environment
    python run.py development        # Uses development environment
    python run.py production         # Uses production environment
"""
import os
import sys
import uvicorn

def main():
    # Parse command line arguments
    if len(sys.argv) > 1:
        env_arg = sys.argv[1].lower()
        if env_arg in ['prod', 'production']:
            env = 'production'
        elif env_arg in ['dev', 'development']:
            env = 'development'
        else:
            print(f"❌ Invalid environment: {env_arg}")
            print("Valid options: dev, development, prod, production")
            sys.exit(1)
    else:
        env = 'development'  # Default to development
    
    # Set environment variable
    os.environ['ENVIRONMENT'] = env
    
    # Import settings after setting environment
    from app.config import settings
    
    print(f"🚀 Starting PastPort Data Processor in {env} mode...")
    print(f"📡 Server will run on {settings.host}:{settings.port}")
    print(f"🐛 Debug mode: {settings.debug}")
    print(f"🌐 CORS origins: {settings.cors_origins}")
    print(f"🗄️  Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print("-" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )

if __name__ == "__main__":
    main()
