from fastapi import APIRouter, Depends
from app.auth_utils import verify_swagger_credentials

router = APIRouter()


@router.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(user: str = Depends(verify_swagger_credentials)):
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")