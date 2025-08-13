import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database Configuration
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(25060, env="DB_PORT")
    db_name: str = Field(..., env="DB_NAME")
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    db_ssl_mode: str = Field("REQUIRED", env="DB_SSL_MODE")
    
    # Application Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default_factory=list, env="CORS_ORIGINS")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    debug: bool = Field(False, env="DEBUG")
    
    @property
    def database_url(self) -> str:
        """Construct the database URL for async MySQL connection"""
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?ssl_ca=&ssl_cert=&ssl_key=&ssl_check_hostname=false&ssl_verify_cert=false"
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        env_file = ".env.prod"
    elif env == "development":
        env_file = ".env.dev"
    else:
        env_file = ".env"
    
    return Settings(_env_file=env_file)


# Global settings instance
settings = get_settings()
