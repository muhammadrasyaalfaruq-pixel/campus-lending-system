from app.main import app
from mangum import Mangum

# Wrap FastAPI with Mangum for serverless
app = Mangum(app, lifespan="off")
