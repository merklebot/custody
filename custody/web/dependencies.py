from typing import Generator, Generic, Optional, Tuple, TypeVar
from starlette.requests import Request
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import Depends

from sqlalchemy.orm import Session

from custody.db.session import SessionLocal
from custody.db.models.user import User


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class ApiKey:
    async def __call__(self, request: Request)->Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        return param

api_key_token_scheme = ApiKey()

async def get_current_user(api_key: str = Depends(api_key_token_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    user = db.query(User).filter(User.api_key == api_key).first()
    return user
