import binascii
import os
import shutil
import subprocess
from typing import List

import httpx
import hvac
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from pydantic import BaseModel
from tqdm import tqdm

from custody.core.config import settings
from custody.logger import logger
from custody.utils import (
    get_data_from_instant_storage,
    get_ipfs_file_info,
    parse_boost_result,
    parse_lassie_result,
    upload_car_to_public_storage,
)

client = hvac.Client(
    url=settings.VAULT_ADDRESS,
    token=settings.VAULT_TOKEN,
)


class ContentPack(BaseModel):
    pack_uuid: str
    tenant_name: str
    contents: List[str]  # list of original ipfs cids


class ContentEncryptionResult(BaseModel):
    original_cid: str
    encrypted_cid: str
    encrypted_size: int


class GeneratedCar(BaseModel):
    pack_uuid: str
    encrypted_contents: List[ContentEncryptionResult]
    root_cid: str
    comm_p: str
    piece_size: int
    car_size: int


def lassie_fetch_data(cid, output_filepath):
    logging_extra = {"action": "FETCHING_FROM_FILECOIN", "cid": cid}
    logger.info(f"start fetching {cid} from filecoin", extra=logging_extra)
    command = ["lassie", "fetch", "-o", f"{output_filepath}", f"{cid}"]

    lassie_res = (
        subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()
    )

    duration, blocks_number, size = parse_lassie_result(lassie_res)
    logger.info(
        f"fetched {cid} from filecoin, duration={duration}, size={size}",
        extra=logging_extra,
    )
    return duration, blocks_number, size


def extract_content_from_car(car_path, cid, output_path):
    command = ["npx", "ipfs-car", "unpack", car_path, "-r", cid, "-o", output_path]
    res = subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()
    print(res)


def restore_content(original_cid: str):
    logging_extra = {"action": "RESTORING_CONTENT", "original_cid": original_cid}
    secret_key, encrypted_cid, iv = get_encryption_info(original_cid)
    logger.info("got encryption data", extra=logging_extra)
    enc_car_filepath = f"tmp/{encrypted_cid}.car"
    enc_filepath = f"tmp/{encrypted_cid}"
    original_filepath = f"tmp/{original_cid}"

    try:
        duration, blocks_number, size = lassie_fetch_data(
            encrypted_cid, enc_car_filepath
        )
        extract_content_from_car(enc_car_filepath, encrypted_cid, enc_filepath)
        os.remove(enc_car_filepath)
    except Exception as e:
        print(e.__traceback__)
        with open(enc_filepath, "wb") as download_file:
            url = f"{os.getenv('IPFS_GATEWAY_URL')}/{encrypted_cid}?stream=true"
            print("fetching from ipfs", url)
            with httpx.stream("GET", url) as response:
                total = int(response.headers["Content-Length"])

                with tqdm(
                    total=total, unit_scale=True, unit_divisor=1024, unit="B"
                ) as progress:
                    num_bytes_downloaded = response.num_bytes_downloaded
                    for chunk in response.iter_bytes():
                        download_file.write(chunk)
                        progress.update(
                            response.num_bytes_downloaded - num_bytes_downloaded
                        )
                        num_bytes_downloaded = response.num_bytes_downloaded

    decrypt_file(
        original_filepath,
        open(enc_filepath, "rb"),
        secret_key,
    )
    os.remove(enc_filepath)
    calculated_cid, calculated_size = get_ipfs_file_info(original_filepath)
    if calculated_cid != original_cid:
        raise Exception(
            f"Got calculated_cid={calculated_cid}"
            f" and original_cid={original_cid} mismatch"
        )

    logger.info(
        f"retrieved and decrypted content with original_cid={original_cid},"
        f" calculated_cid={calculated_cid}",
        extra=logging_extra,
    )
    os.remove(original_filepath)


def make_car(pack_folder: str, pack_uuid: str):
    logging_extra = {"action": "CAR_CREATION", "pack_uuid": pack_uuid}
    logger.info(f"start preparing car {pack_uuid}", extra=logging_extra)
    command = [
        "npx",
        "ipfs-car",
        "pack",
        pack_folder,
        "--output",
        f"./tmp/{pack_uuid}.car",
        "--wrap",
        "false",
    ]
    root_cid = (
        subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()
    ).split("\n")[0]
    logger.info(
        f"generated car {pack_uuid}.car, root_cid: {root_cid}", extra=logging_extra
    )

    command = ["boostx", "commp", f"./tmp/{pack_uuid}.car"]
    boost_res = (
        subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()
    )
    logger.info(
        f"calculated comm_p for {pack_uuid}.car, boost_res: {boost_res}",
        extra=logging_extra,
    )

    comm_p, piece_size, car_size = parse_boost_result(boost_res)

    return root_cid, comm_p, piece_size, car_size


def encrypt_file(file_out_path: str, file_input, secret_key, iv):
    aes = AES.new(secret_key, AES.MODE_CBC, iv)
    filesize = str(file_input.getbuffer().nbytes).zfill(16)
    with open(file_out_path, "wb") as fout:
        sz = 2048
        fout.write(iv)
        fout.write(filesize.encode("utf-8"))
        while True:
            data = file_input.read(sz)
            n = len(data)
            if n == 0:
                break
            elif len(data) % 16 != 0:
                data += b" " * (16 - (len(data) % 16))
            encd = aes.encrypt(data)
            fout.write(encd)
        file_input.close()


def decrypt_file(file_out_path: str, file_input, secret_key):
    with open(file_out_path, "wb") as fout:
        iv = file_input.read(16)
        aes = AES.new(secret_key, AES.MODE_CBC, iv)
        sz = 2048
        filesize = int(file_input.read(16))

        with tqdm(
            total=filesize, unit_scale=True, unit_divisor=1024, unit="B"
        ) as progress:
            while True:
                data = file_input.read(sz)
                n = len(data)
                if n == 0:
                    break
                decrypted_data = aes.decrypt(data)
                fout.write(decrypted_data)

                progress.update(sz)

        fout.truncate(filesize)
        file_input.close()


def get_encryption_info(original_cid):
    read_response = client.secrets.kv.v2.read_secret_version(path=f"{original_cid}")
    iv = binascii.a2b_base64(read_response["data"]["data"]["iv"])
    secret_key = binascii.a2b_base64(read_response["data"]["data"]["secret_key"])
    encrypted_cid = read_response["data"]["data"]["encrypted_cid"]
    return secret_key, encrypted_cid, iv


def process_content_encryption(original_cid, pack_uuid):
    logging_extra = {"action": "CONTENT_ENCRYPTION", "pack_uuid": pack_uuid}
    file_path = f"./tmp/{pack_uuid}/{original_cid}"

    secret_key = get_random_bytes(16)
    iv = get_random_bytes(16)
    saved_encrypted_cid = None
    try:
        secret_key, saved_encrypted_cid, iv = get_encryption_info(original_cid)
    except Exception:
        pass

    logger.info(f"original_cid={original_cid}| got secret key", extra=logging_extra)

    _file = get_data_from_instant_storage(original_cid)
    logger.info(f"original_cid={original_cid}| downloaded data", extra=logging_extra)

    encrypt_file(file_path, _file, secret_key, iv)
    logger.info(f"original_cid={original_cid}| encrypted data", extra=logging_extra)

    encrypted_cid, encrypted_size = get_ipfs_file_info(file_path)
    logger.info(
        f"original_cid={original_cid}| got ipfs info, encrypted_cid={encrypted_cid},"
        f" encrypted_size={encrypted_size}",
        extra=logging_extra,
    )

    if saved_encrypted_cid and saved_encrypted_cid != encrypted_cid:
        err_text = (
            f"original_cid={original_cid}|"
            f" saved_encrypted_cid and encrypted_cid mismatch"
            f", saved_encrypted_cid={saved_encrypted_cid},"
            f" encrypted_cid={encrypted_cid}"
        )
        logger.error(err_text, extra=logging_extra)
        raise Exception(err_text)

    client.secrets.kv.v2.create_or_update_secret(
        path=f"{original_cid}",
        secret=dict(
            encrypted_cid=encrypted_cid,
            secret_key=binascii.b2a_base64(secret_key).decode("utf-8").strip(),
            iv=binascii.b2a_base64(iv).decode("utf-8").strip(),
        ),
    )

    return ContentEncryptionResult(
        original_cid=original_cid,
        encrypted_cid=encrypted_cid,
        encrypted_size=encrypted_size,
    )


def process_storage_pack(content_pack: ContentPack):
    logging_extra = {"action": "PACK_PROCESSING", "pack_uuid": content_pack.pack_uuid}
    logger.info(
        f"start processing pack {content_pack.pack_uuid}, "
        f"contents: {content_pack.contents}",
        extra=logging_extra,
    )
    pack_folder = f"./tmp/{content_pack.pack_uuid}"
    os.mkdir(pack_folder)
    encrypted_contents = []

    for ipfs_cid in content_pack.contents:
        content_encryption_result = process_content_encryption(
            ipfs_cid, content_pack.pack_uuid
        )
        encrypted_contents.append(content_encryption_result)

    root_cid, comm_p, piece_size, car_size = make_car(
        pack_folder, content_pack.pack_uuid
    )

    car = GeneratedCar(
        pack_uuid=content_pack.pack_uuid,
        encrypted_contents=encrypted_contents,
        root_cid=root_cid,
        comm_p=comm_p,
        piece_size=piece_size,
        car_size=car_size,
    )

    logger.info(
        f"Generated .car {content_pack.pack_uuid}. {car.dict()} ", extra=logging_extra
    )

    shutil.rmtree(pack_folder)

    upload_car_to_public_storage(content_pack.pack_uuid)
    os.remove(f"./tmp/{content_pack.pack_uuid}.car")
    return car.dict()
