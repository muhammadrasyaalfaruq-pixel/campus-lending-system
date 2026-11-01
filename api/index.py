import sys
import traceback
from pathlib import Path

# Add parent dir so `app` can be imported when running from `api/`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from mangum import Mangum
    from app.main import app
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # Expose import errors for debugging
    error_msg = f"Import failed: {str(e)}\n{traceback.format_exc()}"
    
    def handler(event, context):
        return {
            "statusCode": 500,
            "body": error_msg
        }
