"""
Central settings object. Reads from .env so nothing is hardcoded.
Import `settings` anywhere you need a config value:

    from app.config import settings
    print(settings.DEVICE)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Server
    APP_ENV: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Storage
    UPLOAD_DIR: str = "./data/uploads"
    CACHE_DIR: str = "./data/cache"
    MAX_UPLOAD_MB: int = 50

    # Model checkpoints
    VQA_CAPTIONING_MODEL_PATH: str = "./checkpoints/vqa_captioning"
    GROUNDING_MODEL_PATH: str = "./checkpoints/grounding"
    CHANGE_DETECTION_MODEL_PATH: str = "./checkpoints/change_detection"
    OPTICAL_SAR_FUSION_MODEL_PATH: str = "./checkpoints/optical_sar_fusion"
    LAND_SEGMENTATION_MODEL_PATH: str = "./checkpoints/land_segmentation"

    # Device
    DEVICE: str = "cpu"

    # Orchestrator
    ORCHESTRATOR_LLM: str = "gpt-4o-mini"
    ORCHESTRATOR_CONFIDENCE_THRESHOLD: float = 0.55


settings = Settings()

