"""
Config loader — reads config.yaml and .env into a single typed object.

Usage anywhere in the project:

    from video2notes.utils.config import load_config
    cfg = load_config()
    print(cfg.whisper.model_size)
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Sub-models — one per section of config.yaml

class PathsConfig(BaseModel):
    data_dir: Path = Path("data")
    output_dir: Path = Path("output")
    cache_dir: Path = Path(".cache")


class WhisperConfig(BaseModel):
    model_config = {"protected_namespaces": ()}   # silence Pydantic warning

    model_size: str = "base"
    language: Optional[str] = None
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 5

class ScenesConfig(BaseModel):
    threshold: float = 27.0
    min_scene_length: float = 30.0


class KeyframesConfig(BaseModel):
    position: str = "middle"
    quality: int = 90
    max_width: int = 1280


class AIConfig(BaseModel):
    model_config = {"protected_namespaces": ()}   # silence Pydantic warning

    enabled: bool = True
    backend: str = "ollama"
    model: str = "llama3.1:8b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.3
    max_retries: int = 2

class OutputConfig(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ["markdown"])
    embed_frames: bool = True
    include_transcript: bool = False


# Top-level Config

class Config(BaseModel):
    paths: PathsConfig = PathsConfig()
    whisper: WhisperConfig = WhisperConfig()
    scenes: ScenesConfig = ScenesConfig()
    keyframes: KeyframesConfig = KeyframesConfig()
    ai: AIConfig = AIConfig()
    output: OutputConfig = OutputConfig()

    # Secrets from .env
    openai_api_key: Optional[str] = None
    hf_token: Optional[str] = None
    log_level: str = "INFO"


def load_config(config_path: Path = Path("config.yaml")) -> Config:
    """Load YAML config + .env into a single Config object."""
    # Load .env into os.environ (does nothing if .env is missing)
    load_dotenv()

    # Read the YAML file
    data: dict = {}
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    # Merge environment-based secrets into the config dict
    data["openai_api_key"] = os.getenv("OPENAI_API_KEY") or None
    data["hf_token"] = os.getenv("HF_TOKEN") or None
    data["log_level"] = os.getenv("LOG_LEVEL", "INFO")

    return Config(**data)