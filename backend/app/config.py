"""Application configuration from environment variables."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)


class Settings:
    """Application settings loaded from environment with safe defaults."""
    
    # Database - Safe defaults for local development
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
    DB_NAME: str = os.environ.get('DB_NAME', 'dhan_draft_db')
    
    # Security
    JWT_SECRET: str = os.environ.get(
        'JWT_SECRET', 
        'INSECURE-DEFAULT-SECRET-CHANGE-IN-PRODUCTION'
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', '*')
    
    def __init__(self):
        """Initialize and validate settings."""
        # Warn about default JWT secret
        if self.JWT_SECRET == 'INSECURE-DEFAULT-SECRET-CHANGE-IN-PRODUCTION':
            logger.warning(
                "⚠️  Using default JWT_SECRET! Set JWT_SECRET environment "
                "variable in production!"
            )
        
        # Log configuration (hide sensitive data)
        logger.info(f"MongoDB URL: {self._mask_connection_string(self.MONGO_URL)}")
        logger.info(f"Database: {self.DB_NAME}")
        logger.info(f"CORS Origins: {self.CORS_ORIGINS}")
    
    @staticmethod
    def _mask_connection_string(url: str) -> str:
        """Mask password in connection string for logging."""
        if '@' in url and '://' in url:
            parts = url.split('://', 1)
            if len(parts) == 2:
                protocol, rest = parts
                if '@' in rest:
                    credentials, host = rest.rsplit('@', 1)
                    return f"{protocol}://*****@{host}"
        return url
    
    @property
    def cors_origins_list(self) -> list:
        """Convert CORS_ORIGINS string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]


settings = Settings()
