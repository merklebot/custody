from pydantic import BaseModel


class NewContent(BaseModel):
    name: str
    original_cid: str
