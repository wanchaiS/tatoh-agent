import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Resolves to agent_api/static/ regardless of CWD
STATIC_DIR = Path(__file__).parent.parent / "static"
