from fastapi import APIRouter

from custody.services.storage import StorageManager
from custody.web.schemas.content import EncryptContentPack

router = APIRouter()
storage_manager = StorageManager()


@router.post("/methods/encrypt_content_pack")
async def process_content_encryption(
    process_encryption_req: EncryptContentPack,
):
    result = await storage_manager.process_storage_pack(
        process_encryption_req.uuid, process_encryption_req.contents
    )
    print(result)
    return {
        "pack_uuid": result["pack_uuid"],
        "encrypted_contents": result["encrypted_contents"],
        "root_cid": result["root_cid"],
        "comm_p": result["comm_p"],
        "piece_size": result["piece_size"],
        "car_size": result["car_size"],
    }
