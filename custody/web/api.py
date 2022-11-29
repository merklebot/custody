from fastapi import APIRouter

from custody.web.endpoints import content, keys, users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users")
api_router.include_router(content.router, prefix="/content")
api_router.include_router(keys.router, prefix="/keys")
