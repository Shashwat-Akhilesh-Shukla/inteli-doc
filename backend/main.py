import uvicorn
from fastapi import FastAPI
from backend.api.routes import api_router, ws_router
from backend.api.middleware import setup_middlewares

app = FastAPI(
    title="Intelligent Documentation Navigator API",
    description="Backend Gateway for Agentic Hybrid RAG services.",
    version="1.0.0"
)

# Initialize CORS and SlowAPI Rate Limiting 
setup_middlewares(app)

# Include Routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
