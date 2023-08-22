import binascii
import time

import httpx

from custody.core.config import settings
from custody.services.storage import (
    ContentPack,
    decrypt_file,
    get_encryption_info,
    process_storage_pack,
)


def main():
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


if __name__ == "__main__":
    cid = "bafybeicbwsosaghgjvg7t3awagwihaiuuf2tfa4yn3fpcjbb7ifgla3mki"
    secret_key, encrypted_cid = get_encryption_info(cid)
    print(binascii.b2a_base64(secret_key).decode("utf-8").strip())
    decrypt_file(
        "tmp/archive.zip",
        open(f"tmp/afd9a978-2ec0-40f9-9272-809db492560a/{cid}", "rb"),
        secret_key,
    )
    # main()

    # uvicorn.run(app, host="0.0.0.0", port=8000)
