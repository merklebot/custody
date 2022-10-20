from typing import Optional

from pydantic import BaseModel


class NewContent(BaseModel):
    name: str
    original_cid: str


class PrepareEncryption(BaseModel):
    key_id: Optional[int]
