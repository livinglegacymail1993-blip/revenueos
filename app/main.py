from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, Response

from routers import router, analyze_router, connect_router

app = FastAPI()

_BASE_DIR = Path(__file__).resolve().parent.parent


def _read_ui(name: str) -> str:
    path = _BASE_DIR / "ui" / name
    return path.read_text(encoding="utf-8")


@app.head("/")
def root_head():
    """Render health checks (e.g. HEAD /) return 200."""
    return Response(status_code=200)


@app.get("/", response_class=HTMLResponse)
def root():
    """Landing page."""
    return HTMLResponse(_read_ui("index.html"))


@app.get("/console", response_class=HTMLResponse)
def console_page():
    """Operator console."""
    return HTMLResponse(_read_ui("console.html"))


@app.get("/privacy", response_class=HTMLResponse)
def privacy_page():
    """Privacy policy."""
    return HTMLResponse(_read_ui("privacy.html"))


@app.get("/security", response_class=HTMLResponse)
def security_page():
    """Security posture."""
    return HTMLResponse(_read_ui("security.html"))


@app.get("/about")
def about_page():
    """About page."""
    path = _BASE_DIR / "ui" / "about.html"
    return FileResponse(path)


@app.get("/api/root")
def api_root():
    """API discovery."""
    return {
        "name": "RevenueOS",
        "status": "live",
        "docs": "/docs",
        "console": "/console",
        "privacy": "/privacy",
        "security": "/security",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(connect_router)
app.include_router(router)
app.include_router(analyze_router)
