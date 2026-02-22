"""
ACDIH Configuration Manager with Environment Validation
Handles all configuration, environment variables, and secrets management
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Main configuration class with validation"""
    
    # Firebase Configuration
    firebase_project_id: str = Field(..., env="FIREBASE_PROJECT_ID")
    firebase_private_key: str = Field(..., env="FIREBASE_PRIVATE_KEY")
    firebase_client_email: str = Field(..., env="FIREBASE_CLIENT_EMAIL")
    firestore_database_url: str = Field(
        "https://firestore.googleapis.com",
        env="FIRESTORE_DATABASE_URL"
    )
    
    # Graph Configuration
    max_graph_nodes: int = Field(1000000, env="MAX_GRAPH_NODES")
    max_graph_edges: int = Field(5000000, env="MAX_GRAPH_EDGES")
    graph_cache_ttl: int = Field(300, env="GRAPH_CACHE_TTL")
    
    # Discovery Configuration
    causal_confidence_threshold: float = Field(0.8, env="CAUSAL_CONFIDENCE_THRESHOLD")
    correlation_threshold: float = Field(0.7, env="CORRELATION_THRESHOLD")
    discovery_batch_size: int = Field(1000, env="DISCOVERY_BATCH_SIZE")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("acdih_synaptic.log", env="LOG_FILE")
    
    # Performance Configuration
    max_workers: int = Field(os.cpu_count() or 4, env="MAX_WORKERS")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    @validator('causal_confidence_threshold')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")
        return v
    
    @validator('correlation_threshold')
    def validate_correlation(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Correlation threshold must be between 0 and 1")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@dataclass
class FirebaseCredentials:
    """Validated Firebase credentials container"""
    project_id: str
    private_key: str
    client_email: str
    
    @classmethod
    def from_settings(cls, settings: Settings) -> 'FirebaseCredentials':
        """Create credentials from settings with validation"""
        if not all([settings.firebase_project_id, 
                   settings.firebase_private_key, 
                   settings.firebase_client_email]):
            raise ValueError("Missing Firebase credentials in configuration")
        
        # Validate private key format (starts with -----BEGIN PRIVATE KEY-----)
        if not settings.firebase_private_key.startswith("-----BEGIN PRIVATE KEY-----"):
            logger.warning("Firebase private key may be incorrectly formatted")
        
        return cls(
            project_id=settings.firebase_project_id,
            private_key=settings.firebase_private_key,
            client_email=settings.firebase_client_email
        )


class ConfigManager:
    """Singleton configuration manager with caching"""
    
    _instance = None
    _settings: Optional[Settings] = None
    _credentials: Optional[FirebaseCredentials] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._settings:
            self._load_settings()
    
    def _load_settings(self) -> None:
        """Load and validate settings from environment"""
        try:
            self._settings = Settings()
            self._credentials = FirebaseCredentials.from_settings(self._settings)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    @property
    def settings(self) -> Settings:
        """Get validated settings"""
        if not self._settings:
            self._load_settings()
        return self._settings
    
    @property
    def firebase_credentials(self) -> FirebaseCredentials:
        """Get validated Firebase credentials"""
        if not self._credentials:
            self._load_settings()
        return self._credentials
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration dictionary"""
        return {
            'url': self.settings.redis_url,
            'decode_responses': True,
            'max_connections': self.settings.max_workers * 2
        }


# Global configuration instance
config = ConfigManager()