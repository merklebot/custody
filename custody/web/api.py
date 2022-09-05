from fastapi import APIRouter
from custody.web.endpoints import users
from custody.web.endpoints import content

api_router = APIRouter()
api_router.include_router(users.router, prefix='/users')
api_router.include_router(content.router, prefix='/content')
