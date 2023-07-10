from typing import Optional

from pydantic import BaseModel


class NewContent(BaseModel):
    name: str
    original_cid: str


class PrepareEncryption(BaseModel):
    key_id: Optional[int]


class ProcessEncryption(BaseModel):
    original_cid: Optional[str]
    webhook_url: Optional[str]


class ProcessDecryption(BaseModel):
    aes_key: Optional[str]
    original_cid: Optional[str]
    webhook_url: Optional[str]


class Content(BaseModel):
    ipfs_cid: str
    ipfs_file_size: int


class EncryptContentPack(BaseModel):
    uuid: str
    contents: list[Content]
