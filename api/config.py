import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env si existe localmente
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
API_TITLE = os.getenv("API_TITLE", "AlphaQuant - AI Agent Market API")
API_VERSION = os.getenv("API_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
