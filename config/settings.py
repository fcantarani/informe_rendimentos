"""
config/settings.py
------------------
Central configuration using pydantic.BaseSettings.  Environment variables are
loaded from a `.env` file in the project root; validation, defaulting and
conversion are handled automatically.  This file exports a single `settings`
instance that the rest of the codebase can import.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

# pydantic 2+ moved BaseSettings into separate package
# install 'pydantic-settings' which reexports the original class
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ── directories ─────────────────────────────────────────────────────────
    INPUT_DIR: Path = BASE_DIR / "input"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    SENT_DIR: Path = BASE_DIR / "sent"
    SENT_SUCCESS: Path = SENT_DIR / "success"
    SENT_FAILURE: Path = SENT_DIR / "failure"
    TEMPLATE_DIR: Path = BASE_DIR / "templates"

    # ── oracle configuration ─────────────────────────────────────────────────
    ORACLE_USER: str
    ORACLE_PWD: str
    ORACLE_DSN: str
    ORACLE_WALLET_LOCATION: Optional[str] = None
    ORACLE_WALLET_PASSWORD: Optional[str] = None

    # ── email / AWS SES -----------------------------------------------------
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_USE_TLS: bool = True
    EMAIL_USER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "sa-east-1"

    MODO_TESTE: bool = False
    EMAIL_TESTE: Optional[str] = None

    # ── business values ----------------------------------------------------
    NOME_EMPRESA: str = "CLARO PAY INSTITUICAO DE PAGAMENTO SA"
    ANO_CALENDARIO: str = "2025"

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # allow unrelated env vars


# single, shared settings object
settings = Settings()

# convenience constants for backwards compatibility
INPUT_DIR = settings.INPUT_DIR
OUTPUT_DIR = settings.OUTPUT_DIR
SENT_DIR = settings.SENT_DIR
SENT_SUCCESS = settings.SENT_SUCCESS
SENT_FAILURE = settings.SENT_FAILURE
TEMPLATE_DIR = settings.TEMPLATE_DIR
NOME_EMPRESA = settings.NOME_EMPRESA
ANO_CALENDARIO = settings.ANO_CALENDARIO

