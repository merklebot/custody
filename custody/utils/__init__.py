import io
import re

import boto3
import httpx

from custody.core.config import settings


def get_data_from_instant_storage(ipfs_cid):
    client = boto3.client(
        service_name="s3",
        region_name=settings.INSTANT_STORAGE_REGION,
        endpoint_url=settings.INSTANT_STORAGE_ENDPOINT,
        aws_access_key_id=settings.INSTANT_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.INSTANT_STORAGE_SECRET_ACCESS_KEY,
    )
    _file = io.BytesIO()
    client.download_fileobj(settings.INSTANT_STORAGE_BUCKET_NAME, ipfs_cid, _file)
    _file.seek(0)
    return _file


def upload_car_to_public_storage(pack_uuid):
    path = f"./tmp/{pack_uuid}.car"
    s3_key = f"{pack_uuid}.car"
    client = boto3.client(
        service_name="s3",
        region_name=settings.PUBLIC_STORAGE_REGION,
        endpoint_url=settings.PUBLIC_STORAGE_ENDPOINT,
        aws_access_key_id=settings.PUBLIC_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.PUBLIC_STORAGE_SECRET_ACCESS_KEY,
    )
    with open(path, "rb") as spfp:
        client.upload_fileobj(
            spfp,
            settings.PUBLIC_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ACL": "public-read"},
        )


def upload_file_to_instant_storage(path, cid):
    client = boto3.client(
        service_name="s3",
        region_name=settings.PUBLIC_STORAGE_REGION,
        endpoint_url=settings.PUBLIC_STORAGE_ENDPOINT,
        aws_access_key_id=settings.PUBLIC_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.PUBLIC_STORAGE_SECRET_ACCESS_KEY,
    )
    with open(path, "rb") as spfp:
        client.upload_fileobj(
            spfp,
            settings.PUBLIC_STORAGE_BUCKET_NAME,
            cid,
        )


def get_ipfs_file_info(file_path):
    with open(file_path, "rb") as file:
        with httpx.Client(
            base_url=settings.IPFS_HTTP_PROVIDER,
        ) as client:
            response = client.post(
                "/api/v0/add",
                params={"cid-version": 1, "only-hash": True},
                files={"upload-files": file},
            )
            result = response.json()
            return result["Hash"], int(result["Size"])


def parse_boost_result(res):
    comm_p = re.findall(r"[\n\r]*CommP CID:*([^\n\r]*)", res)[0].strip()
    piece_size = int(re.findall(r"[\n\r]*Piece size:*([^\n\r]*)", res)[0].strip())
    car_size = int(re.findall(r"[\n\r]*Car file size:*([^\n\r]*)", res)[0].strip())
    return comm_p, piece_size, car_size


def parse_lassie_result(res):
    duration = re.findall(r"[\n\r]*Duration:*([^\n\r]*)", res)[0].strip()
    blocks_number = re.findall(r"[\n\r]*Blocks:*([^\n\r]*)", res)[0].strip()
    size = re.findall(r"[\n\r]*Bytes:*([^\n\r]*)", res)[0].strip()
    return duration, blocks_number, size
