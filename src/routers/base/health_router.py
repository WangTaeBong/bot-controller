import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.common.config_loader import ConfigLoader

# Load application settings
config_loader = ConfigLoader()
settings = config_loader.get_settings()

# Configure logging
logger = logging.getLogger(__name__)

# Templates directory setup
templates = Jinja2Templates(directory="templates")

# Define health check router
health_router = APIRouter()


@health_router.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Perform a health check to ensure the FastAPI application is running properly.

    Returns:
        JSONResponse: JSON object containing the status and message.
    """
    logger.info("Health check endpoint accessed.")
    try:
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "message": "MAI-Chat BotController is running smoothly."}
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Health check failed due to an internal error."}
        )


@health_router.get("/health_check_ui", include_in_schema=False, response_class=HTMLResponse)
async def health_check_ui(request: Request):
    """
    Perform a health check and display the result in a user-friendly HTML page.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        HTMLResponse: Rendered HTML response showing system health status.
    """

    # Determine the correct protocol based on the configuration
    protocol = "https" if settings.ssl.use_https else "http"

    content = f"""
        <h2>System Health: OK</h2>
        <p>The MAI-Chat BotController is running smoothly on {protocol}.</p>
    """

    try:
        return templates.TemplateResponse("base.html", {
            "request": request,
            "title": "Health Check",
            "content": content
        })
    except Exception as e:
        logger.error(f"Failed to render health check UI: {e}")
        return HTMLResponse(
            status_code=500,
            content="<h2>Error</h2><p>Failed to load health check UI.</p>"
        )
