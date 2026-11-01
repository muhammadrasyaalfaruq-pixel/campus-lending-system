import sys
from pathlib import Path

# Add project root to sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app as fastapi_app
from mangum import Mangum

# Wrap FastAPI with Mangum for serverless
handler = Mangum(fastapi_app, lifespan="off")
app = handler
