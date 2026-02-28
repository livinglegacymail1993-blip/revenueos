from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from routers import router, analyze_router

app = FastAPI()


@app.get("/")
def root():
    """Redirect browsers to the Operator Console; API discovery remains at /api/root."""
    return RedirectResponse(url="/ui", status_code=302)


@app.get("/api/root")
def api_root():
    """API discovery: name, status, docs, demo, ui."""
    return {
        "name": "RevenueOS",
        "status": "live",
        "docs": "/docs",
        "demo": "POST /analyze/demo",
        "ui": "/ui",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/ui", response_class=HTMLResponse)
def ui_console():
    """Serve the minimal Operator Console UI."""
    base_dir = Path(__file__).resolve().parent.parent
    html_path = base_dir / "ui" / "console.html"
    html = html_path.read_text(encoding="utf-8")
    return html


app.include_router(router)
app.include_router(analyze_router)
