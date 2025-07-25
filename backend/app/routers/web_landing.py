from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, FileResponse
from app.dependencies import get_optional_user
import os

router = APIRouter()

@router.get("/", include_in_schema=False)
async def landing_page(request: Request, current_user=Depends(get_optional_user)):
    if current_user:
        return RedirectResponse(url="/app")
    # Serve the static HTML file (absolute path for FileResponse)
    landing_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../lms_evo_landing.html'))
    return FileResponse(landing_path, media_type="text/html") 