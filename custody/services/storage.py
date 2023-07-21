import binascii
import io
import os
import re
import shutil
import subprocess

import aioboto3
import httpx
import hvac
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

from custody.core.config import settings
from custody.logger import logger

client = hvac.Client(
    url=settings.VAULT_ADDRESS,
    token=settings.VAULT_TOKEN,
)


def parse_boost_result(res):
    comm_p = re.findall(r"[\n\r]*CommP CID:*([^\n\r]*)", res)[0].strip()
    piece_size = re.findall(r"[\n\r]*Piece size:*([^\n\r]*)", res)[0].strip()
    car_size = re.findall(r"[\n\r]*Car file size:*([^\n\r]*)", res)[0].strip()
    return comm_p, piece_size, car_size


def make_car(pack_folder: str, pack_id: str):
    logger.info(f"preparing car {pack_id}")

    command = [
        "npx",
        "ipfs-car",
        "pack",
        pack_folder,
        "--output",
        f"./tmp/{pack_id}.car",
        "--wrap",
        "false",
    ]
    logger.info(f"executing command {command}")
    ipfs_car_res = (
        subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()
    )
    logger.info(f"root_cid {ipfs_car_res}")

    command = ["boostx", "commp", f"./tmp/{pack_id}.car"]
    logger.info(f"executing command {command}")
    try:
        boost_res = (
            subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()
        )
    except subprocess.CalledProcessError as e:
        logger.info(e.output)

    logger.info(f"boost_res {boost_res}")
    comm_p, piece_size, car_size = parse_boost_result(boost_res)

    return ipfs_car_res, comm_p, piece_size, car_size


async def get_ipfs_file_info(file):
    async with httpx.AsyncClient(
        base_url=settings.IPFS_HTTP_PROVIDER,
    ) as client:
        response = await client.post(
            "/api/v0/add",
            params={"cid-version": 1, "only-hash": True},
            files={"upload-files": file},
        )
        return response.json()


async def get_data_from_instant_storage(ipfs_cid):
    logger.info(f"getting object {ipfs_cid}")
    async with aioboto3.Session().client(
        service_name="s3",
        region_name=settings.INSTANT_STORAGE_REGION,
        endpoint_url=settings.INSTANT_STORAGE_ENDPOINT,
        aws_access_key_id=settings.INSTANT_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.INSTANT_STORAGE_SECRET_ACCESS_KEY,
    ) as s3:
        _file = io.BytesIO()
        await s3.download_fileobj(settings.INSTANT_STORAGE_BUCKET_NAME, ipfs_cid, _file)
        _file.seek(0)
        return _file


async def upload_car_to_public_storage(pack_uuid):
    path = f"./tmp/{pack_uuid}.car"
    s3_key = f"{pack_uuid}.car"
    logger.info(f"uplaoding {path}")
    async with aioboto3.Session().client(
        service_name="s3",
        region_name=settings.PUBLIC_STORAGE_REGION,
        endpoint_url=settings.PUBLIC_STORAGE_ENDPOINT,
        aws_access_key_id=settings.PUBLIC_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.PUBLIC_STORAGE_SECRET_ACCESS_KEY,
    ) as s3:
        with open(path, "rb") as spfp:
            await s3.upload_fileobj(spfp, settings.PUBLIC_STORAGE_BUCKET_NAME, s3_key)


class StorageManager:
    async def process_storage_pack(self, pack_uuid, contents):
        pack_folder = f"./tmp/{pack_uuid}"
        os.mkdir(pack_folder)
        encrypted_contents = []
        for ipfs_cid in contents:
            res = await self.process_encryption(ipfs_cid, pack_folder)
            encrypted_contents.append(res)
        logger.info(encrypted_contents)
        root_cid, comm_p, piece_size, car_size = make_car(pack_folder, pack_uuid)
        shutil.rmtree(pack_folder)

        await upload_car_to_public_storage(pack_uuid)
        os.remove(f"./tmp/{pack_uuid}.car")
        return {
            "pack_uuid": pack_uuid,
            "encrypted_contents": encrypted_contents,
            "root_cid": root_cid,
            "comm_p": comm_p,
            "piece_size": piece_size,
            "car_size": car_size,
        }

    async def process_encryption(self, original_cid, pack_folder):
        file_path = f"{pack_folder}/{original_cid}"
        file_out = open(file_path, "wb")

        rsa_key = RSA.generate(2048)
        cipher_rsa = PKCS1_OAEP.new(rsa_key)
        secret_data = rsa_key.export_key()
        session_key = get_random_bytes(16)
        enc_session_key = cipher_rsa.encrypt(session_key)

        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        logger.info("start getting data")
        _file = await get_data_from_instant_storage(original_cid)
        res = _file.read()

        ciphertext, tag = cipher_aes.encrypt_and_digest(res)
        [
            file_out.write(x)
            for x in (enc_session_key, cipher_aes.nonce, tag, ciphertext)
        ]
        file_out.close()
        logger.info("file encrypted")

        encrypted_info = await get_ipfs_file_info(open(file_path, "rb"))

        encrypted_cid = encrypted_info["Hash"]
        encrypted_size = encrypted_info["Size"]

        create_response = client.secrets.kv.v2.create_or_update_secret(
            path=f"{original_cid}",
            secret=dict(
                encrypted_cid=encrypted_cid,
                secret_data=binascii.b2a_base64(secret_data).decode("utf-8").strip(),
                aes_key=binascii.b2a_base64(enc_session_key).decode("utf-8").strip(),
            ),
        )
        logger.info(create_response)

        logger.info("content encryption finished")

        # os.remove(file_path)

        result = {
            "original_cid": original_cid,
            "encrypted_cid": encrypted_cid,
            "encrypted_size": encrypted_size,
        }

        return result
