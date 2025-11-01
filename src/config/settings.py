from pydantic_settings import BaseSettings
from typing import Optional
import pathlib
from .logger_config import logger

class Settings(BaseSettings):
    HF_TOKEN: Optional[str] = None

config_path = pathlib.Path(__file__).parent / ".env"
settings = Settings(_env_file=config_path, _env_file_encoding='utf-8')
logger.info(f"Settings loaded.")









