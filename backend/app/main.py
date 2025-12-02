"""Main FastAPI application"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .config import settings
from .database import init_db
from .routers import games_router, chat_router
from .websockets import websocket_router

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables"""
    init_db()

# Include routers
app.include_router(games_router)
app.include_router(chat_router)
app.include_router(websocket_router)

# Mount static files and templates
frontend_path = Path(__file__).parent.parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")

templates = Jinja2Templates(directory=str(frontend_path / "templates"))


# Routes for serving HTML pages
@app.get("/")
async def index(request: Request):
    """Serve landing page"""
    # Set session cookie if not exists
    import secrets
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = secrets.token_urlsafe(32)
    
    response = templates.TemplateResponse("index.html", {"request": request})
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=86400 * 7  # 7 days
    )
    return response


@app.get("/game/{game_code}")
async def game_page(request: Request, game_code: str):
    """Serve game page"""
    return templates.TemplateResponse("game.html", {
        "request": request,
        "game_code": game_code
    })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "app": settings.APP_NAME}
