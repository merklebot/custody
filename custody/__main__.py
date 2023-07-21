import asyncio
import time

import httpx

from custody.core.config import settings
from custody.services.storage import StorageManager

storage_manager = StorageManager()


async def main():
    while True:
        with httpx.Client() as client:
            car_resp = client.get(
                settings.STORAGE_BACKEND_URL + "/internal/filecoin.getCarToProcess",
                headers={"Authorization": settings.STORAGE_ADMIN_TOKEN},
            )
            car = car_resp.json()
        if car:
            result = await storage_manager.process_storage_pack(
                car["pack_uuid"], car["contents"]
            )

            storage_resp = client.post(
                settings.STORAGE_BACKEND_URL + "/internal/filecoin.carCreated",
                headers={"Authorization": settings.STORAGE_ADMIN_TOKEN},
                data={
                    "pack_uuid": result["pack_uuid"],
                    "tenant_name": car["tenant_name"],
                    "encrypted_contents": result["encrypted_contents"],
                    "root_cid": result["root_cid"],
                    "comm_p": result["comm_p"],
                    "piece_size": result["piece_size"],
                    "car_size": result["car_size"],
                },
            )

            print(storage_resp.json())
        time.sleep(5)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    # uvicorn.run(app, host="0.0.0.0", port=8000)
