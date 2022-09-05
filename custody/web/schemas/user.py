from pydantic import BaseModel


class NewUser(BaseModel):
    name: str
    email: str
    api_key: str
