import sys
import time

import httpx

from custody.core.config import settings
from custody.services.storage import ContentPack, process_storage_pack, restore_content


def start_content_packs_processing():
    while True:
        with httpx.Client() as client:
            content_pack_resp = client.get(
                settings.STORAGE_BACKEND_URL + "/internal/filecoin.getCarToProcess",
                headers={"Authorization": settings.STORAGE_ADMIN_TOKEN},
            )
            content_pack = content_pack_resp.json()
        if content_pack:
            result = process_storage_pack(ContentPack(**content_pack))
            with httpx.Client() as client:
                car_result = {
                    "pack_uuid": result["pack_uuid"],
                    "tenant_name": content_pack["tenant_name"],
                    "encrypted_contents": result["encrypted_contents"],
                    "root_cid": result["root_cid"],
                    "comm_p": result["comm_p"],
                    "piece_size": result["piece_size"],
                    "car_size": result["car_size"],
                }
                print(car_result)
                storage_resp = client.post(
                    settings.STORAGE_BACKEND_URL + "/internal/filecoin.carCreated",
                    headers={"Authorization": settings.STORAGE_ADMIN_TOKEN},
                    json=car_result,
                )

                print(storage_resp.json())

        time.sleep(5)


def start_content_restoring():
    while True:
        with httpx.Client() as client:
            restore_request_resp = client.post(
                settings.STORAGE_BACKEND_URL + "/internal/filecoin.startRestoreProcess",
                headers={"Authorization": settings.STORAGE_ADMIN_TOKEN},
                json={"worker_instance": settings.WORKER_INSTANCE},
            )
            restore_request = restore_request_resp.json()
            print(restore_request)
            if restore_request:
                status = "done"
                try:
                    restore_content(restore_request["original_cid"])
                except Exception as e:
                    print(e.__traceback__)
                    status = "error"
                client.post(
                    settings.STORAGE_BACKEND_URL
                    + "/internal/filecoin.finishRestoreProcess",
                    headers={"Authorization": settings.STORAGE_ADMIN_TOKEN},
                    json={
                        "worker_instance": settings.WORKER_INSTANCE,
                        "restore_request_id": restore_request["restore_request_id"],
                        "status": status,
                    },
                )
        time.sleep(5)


if __name__ == "__main__":
    if "restore" in sys.argv:
        if "--original_cid" in sys.argv:
            original_cid = sys.argv[3]
            print("restoring", original_cid)
            restore_content(original_cid)
        else:
            start_content_restoring()
    else:
        start_content_packs_processing()
