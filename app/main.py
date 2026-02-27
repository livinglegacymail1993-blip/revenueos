from fastapi import FastAPI

from routers import router, analyze_router

app = FastAPI()


@app.get("/")
def root():
    """Root endpoint for Render and API discovery."""
    return {
        "name": "RevenueOS",
        "status": "live",
        "docs": "/docs",
        "demo": "POST /analyze/demo",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(router)
app.include_router(analyze_router)
