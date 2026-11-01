import sys
from pathlib import Path

# Add project root to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.main import app
    from mangum import Mangum
    # Wrap FastAPI ASGI app with Mangum for AWS Lambda (Vercel runtime)
    handler = Mangum(app)
except Exception as e:
    import traceback
    error_msg = f"Failed to import app: {e}\n{traceback.format_exc()}"
    print(error_msg)
    
    # Fallback ASGI app that returns error
    from mangum import Mangum
    async def fail_app(scope, receive, send):
        await send({
            'type': 'http.response.start',
            'status': 500,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': error_msg.encode(),
        })
    handler = Mangum(fail_app)
