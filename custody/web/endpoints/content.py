from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from custody.db.models.storage import Content
from custody.db.models.user import User
from custody.web import dependencies
from custody.web.schemas.content import NewContent
from custody.services.storage import StorageManager

router = APIRouter()


@router.get('/')
async def list_content(user: User = Depends(dependencies.get_current_user), db: Session = Depends(dependencies.get_db)):
    storage_manager = StorageManager(user, db)
    return storage_manager.list_content()


@router.get('/{content_id}')
async def get_content(content_id: int, user: User = Depends(dependencies.get_current_user),
                      db: Session = Depends(dependencies.get_db)):
    storage_manager = StorageManager(user, db)
    content = storage_manager.get_content(content_id)
    return {
        'original_cid': content.original_cid
    }


@router.post('/{content_id}/methods/prepare_encryption')
async def prepare_content_encryption(content_id: int, user: User = Depends(dependencies.get_current_user),
                      db: Session = Depends(dependencies.get_db)):
    storage_manager = StorageManager(user, db)
    content = storage_manager.get_content(content_id)
    storage_manager.prepare_content_encryption(content)
    return {'result': 'ok'}



@router.post('/')
async def add_content(new_content: NewContent, user: User = Depends(dependencies.get_current_user),
                      db: Session = Depends(dependencies.get_db)):
    storage_manager = StorageManager(user, db)
    content = storage_manager.add_content(new_content.original_cid)
    return {
        'original_cid': content.original_cid
    }
