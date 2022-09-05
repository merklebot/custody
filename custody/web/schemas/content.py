from pydantic import BaseModel


class NewContent(BaseModel):
    original_cid: str
