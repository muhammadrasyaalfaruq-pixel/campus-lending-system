import sys
from pathlib import Path

# Add project root to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.main import app
    from app.main import app as fastapi_app
    from mangum import Mangum
    # Wrap FastAPI ASGI app with Mangum for AWS Lambda (Vercel runtime)
    handler = Mangum(app)
    handler = Mangum(fastapi_app)
    app = handler  # Vercel looks for 'app'
except Exception as e:
    import traceback
    error_msg = f"Failed to import app: {e}\n{traceback.format_exc()}"
    print(error_msg)

 @@ -26,4 +27,5 @@
            'type': 'http.response.body',
            'body': error_msg.encode(),
        })
    handler = Mangum(fail_app)
    app = handler
