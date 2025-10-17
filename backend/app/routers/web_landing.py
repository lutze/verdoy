from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, FileResponse
from app.dependencies import get_optional_user
from app.config import settings
import os
from pathlib import Path

router = APIRouter()

def get_landing_page_path() -> str:
    """
    Get the path to the landing page HTML file.
    
    This function looks for the landing page in the following order:
    1. LANDING_PAGE_PATH environment variable (if set)
    2. Default location in the backend directory
    3. Fallback to a relative path from the current file
    
    Returns:
        str: Absolute path to the landing page HTML file
    """
    # Check for environment variable first
    landing_path_env = os.getenv("LANDING_PAGE_PATH")
    if landing_path_env and os.path.exists(landing_path_env):
        return os.path.abspath(landing_path_env)
    
    # Try to find the landing page in the backend directory
    # Get the backend directory (parent of the app directory)
    backend_dir = Path(__file__).parent.parent.parent
    landing_file = backend_dir / "lms_evo_landing.html"
    
    if landing_file.exists():
        return str(landing_file.absolute())
    
    # Fallback to the original relative path approach
    fallback_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../lms_evo_landing.html'))
    return fallback_path

@router.get("/", include_in_schema=False)
async def landing_page(request: Request, current_user=Depends(get_optional_user)):
    if current_user:
        return RedirectResponse(url="/app")
    
    # Get the landing page path using the robust method
    landing_path = get_landing_page_path()
    
    # Check if the file exists
    if not os.path.exists(landing_path):
        # Return a simple error response if the landing page is not found
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content="<html><body><h1>Landing page not found</h1><p>The landing page file is missing.</p></body></html>",
            status_code=404
        )
    
    return FileResponse(landing_path, media_type="text/html") 