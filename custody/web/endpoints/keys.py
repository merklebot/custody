from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from custody.db.models.user import User
from custody.services.storage import StorageManager
from custody.web import dependencies

router = APIRouter()


@router.get("/")
async def list_keys(
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    storage_manager = StorageManager(user, db)
    return [key.as_dict() for key in storage_manager.list_keys()]


@router.post("/")
async def create_key(
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    storage_manager = StorageManager(user, db)
    key = storage_manager.create_key()
    return key.as_dict()
