import traceback

import aiohttp
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from custody.db.models.user import User
from custody.services.storage import StorageManager
from custody.web import dependencies
from custody.web.schemas.content import NewContent, ProcessDecryption, ProcessEncryption

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


async def process_content_encryption_task(
    db, user, original_cid, aes_key, webhook_url=None
):
    storage_manager = StorageManager(user, db)
    result = None
    status = "finished"
    try:
        result = await storage_manager.process_encryption(original_cid, aes_key)
        print(result)
    except Exception:
        traceback.print_exc()
        status = "error"
    if webhook_url:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url, json={"status": status, "result": result}
            ) as resp:
                print(resp)


async def process_content_decryption_task(
    db, user, original_cid, aes_key, webhook_url=None
):
    storage_manager = StorageManager(user, db)
    result = None
    status = "finished"
    try:
        result = await storage_manager.process_decryption(original_cid, aes_key)
        print(result)
    except Exception:
        traceback.print_exc()
        status = "error"

    if webhook_url:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url, json={"status": status, "result": result}
            ) as resp:
                print(resp)


@router.post("/methods/process_encryption")
async def process_content_encryption(
    process_encryption_req: ProcessEncryption,
    background_tasks: BackgroundTasks,
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    background_tasks.add_task(
        process_content_encryption_task,
        db,
        user,
        process_encryption_req.original_cid,
        process_encryption_req.aes_key,
        process_encryption_req.webhook_url,
    )
    return {"result": "started"}


@router.post("/methods/process_decryption")
async def process_content_decryption(
    process_decryption_req: ProcessDecryption,
    background_tasks: BackgroundTasks,
    user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    background_tasks.add_task(
        process_content_decryption_task,
        db,
        user,
        process_decryption_req.original_cid,
        process_decryption_req.aes_key,
        process_decryption_req.webhook_url,
    )
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
