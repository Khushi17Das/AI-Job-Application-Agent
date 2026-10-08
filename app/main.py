import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
from app.routes import documents, analysis, applications

# Create database tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Job Application Agent",
    description="Portfolio-ready AI agent for CV matching, skill gap analysis, answer generation, and claim verification.",
    version="1.0.0"
)

# Enable CORS for local development (allows Live Server at port 5500 to talk to port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(applications.router)

# Mount frontend directory for static assets
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        """Serves the main frontend single-page interface."""
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend index.html not found. Backend API is active at /docs"}

    @app.get("/style.css", include_in_schema=False)
    def serve_css():
        return FileResponse(os.path.join(FRONTEND_DIR, "style.css"))

    @app.get("/app.js", include_in_schema=False)
    def serve_js():
        return FileResponse(os.path.join(FRONTEND_DIR, "app.js"))
