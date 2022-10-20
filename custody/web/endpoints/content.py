from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from custody.db.models.storage.key import Key
from custody.db.models.user import User
from custody.db.session import SessionLocal
from custody.services.storage import StorageManager
from custody.web import dependencies
from custody.web.schemas.content import NewContent, PrepareEncryption

router = APIRouter()


@router.get("/")
async def list_content(
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    storage_manager = StorageManager(user, db)
    return storage_manager.list_content()


@router.get("/{content_id}")
async def get_content(
    content_id: int,
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    storage_manager = StorageManager(user, db)
    content = storage_manager.get_content(content_id)
    return content.as_dict()


@router.post("/{content_id}/methods/prepare_encryption")
async def prepare_content_encryption(
    content_id: int,
    prepare_encryption_req: PrepareEncryption,
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    key_id = prepare_encryption_req.key_id
    key = None
    if key_id:
        key = db.query(Key).filter(Key.id == key_id).first()
    storage_manager = StorageManager(user, db)
    content = storage_manager.get_content(content_id)
    await storage_manager.prepare_content_encryption(content, key)
    return {"result": "ok"}


async def process_content_encryption_task(user, content_id):
    db = SessionLocal()
    storage_manager = StorageManager(user, db)
    content = storage_manager.get_content(content_id)
    await storage_manager.process_encryption(content)


@router.post("/{content_id}/methods/process_encryption")
async def process_content_encryption(
    content_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(dependencies.get_current_user),
):
    background_tasks.add_task(process_content_encryption_task, user, content_id)
    return {"result": "started"}


async def process_content_decryption_task(user, content_id):
    db = SessionLocal()
    storage_manager = StorageManager(user, db)
    content = storage_manager.get_content(content_id)
    await storage_manager.process_decryption(content)


@router.post("/{content_id}/methods/process_decryption")
async def process_content_decryption(
    content_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(dependencies.get_current_user),
):
    background_tasks.add_task(process_content_decryption_task, user, content_id)
    return {"result": "started"}


@router.get("/{content_id}/download")
async def process_content_download(
    content_id: int,
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    storage_manager = StorageManager(user, db)
    content = storage_manager.get_content(content_id)
    data = await storage_manager.get_content_data(content)

    def iterfile():
        yield data

    return StreamingResponse(
        iterfile(),
        headers={"Content-Disposition": f'attachment; filename="{content.name}"'},
    )


@router.post("/")
async def add_content(
    new_content: NewContent,
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    storage_manager = StorageManager(user, db)
    content = storage_manager.add_content(new_content.original_cid, new_content.name)
    return content.as_dict()
