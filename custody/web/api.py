from fastapi import APIRouter

from custody.web.endpoints import content

api_router = APIRouter()
api_router.include_router(content.router, prefix="/content")
