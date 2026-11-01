import sys
from pathlib import Path

# Add parent dir so `app` can be imported when running from `api/`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mangum import Mangum
from app.main import app

# Vercel looks for a top-level variable named `app`
app = Mangum(app, lifespan="off")
