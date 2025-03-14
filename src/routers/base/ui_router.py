import logging
from fastapi import APIRouter, Request, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.utils.auth_utils import verify_authentication  # Authentication utility

# ================================
#         Logging Configuration
# ================================
logger = logging.getLogger(__name__)

# ================================
#         Template Settings
# ================================
templates = Jinja2Templates(directory="templates")  # Setting up Jinja2 templates

# ================================
#         UI Router Setup
# ================================
ui_router = APIRouter()


@ui_router.get(
    "/menu",
    include_in_schema=False,
    dependencies=[Depends(verify_authentication)],
    response_class=HTMLResponse
)
async def menu_page(request: Request):
    """
    Renders the main menu page after successful authentication.

    This page provides navigation links to other UI pages like Swagger UI and Health Check.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        HTMLResponse: Rendered HTML containing navigation buttons.
    """

    # HTML content with navigation buttons
    menu_content = """
        <div style="text-align: center;">
            <a href='/custom-swagger' class='btn' style='display: inline-block; margin: 10px; padding: 10px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;'>Swagger UI</a><br>
            <a href='/health_check_ui' class='btn' style='display: inline-block; margin: 10px; padding: 10px; background: #28a745; color: white; text-decoration: none; border-radius: 4px;'>Health Check</a><br>
            <a href='/maichat_test_ui' class='btn' style='display: inline-block; margin: 10px; padding: 10px; background: #28a745; color: white; text-decoration: none; border-radius: 4px;'>MAI-Chat Test</a><br>
            <a href='/maichat_stream_test_ui' class='btn' style='display: inline-block; margin: 10px; padding: 10px; background: #28a745; color: white; text-decoration: none; border-radius: 4px;'>MAI-Chat Stream Test</a><br>
        </div>
    """

    # Render the menu page using Jinja2 template
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "MAI-Chat BotController Admin",
            "content": menu_content
        }
    )


@ui_router.get(
    "/custom-swagger",
    include_in_schema=False,
    dependencies=[Depends(verify_authentication)],
    response_class=HTMLResponse
)
async def custom_swagger_page(request: Request):
    """
    Renders the Swagger UI with an additional navigation button.

    This function dynamically generates the OpenAPI URL and customizes
    the Swagger UI by injecting a "Back to Menu" button.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        HTMLResponse: Rendered Swagger UI with additional navigation button.
    """
    try:
        # Dynamically construct the OpenAPI URL
        openapi_url = f"{str(request.base_url).rstrip('/')}/openapi.json"

        # Generate the Swagger UI HTML content
        html_content = get_swagger_ui_html(
            openapi_url=openapi_url,
            title="Swagger UI",
        ).body.decode('utf-8')

        # "Back to Menu" button styling and HTML
        button_html = (
            '<a href="/menu" '
            'style="position: fixed; top: 10px; right: 10px; padding: 10px; background: #007bff; '
            'color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">'
            '⬅ Back to Menu</a>'
        )

        # Inject the button into the HTML content
        html_content = html_content.replace('</body>', f'{button_html}</body>')

        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Failed to render Swagger UI: {e}")  # Log error if rendering fails
        return HTMLResponse(
            content="<h2>Error</h2><p>Failed to load Swagger UI.</p>",
            status_code=500
        )
