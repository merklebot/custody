from typing import List

from sqlalchemy.orm import Session

from custody.db.models.storage import Content
from custody.db.models.user import User
from custody.db.models.storage.key import Key, Secret

import rsa


class StorageManager:
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db

    def add_content(self, original_cid: str) -> Content:
        content = Content(original_cid=original_cid, owner=self.user)
        self.db.add(content)
        self.db.commit()
        return content

    def get_content(self, content_id: int) -> Content:
        return self.db.query(Content).filter(Content.id == content_id and Content.owner_id == self.user.id).first()

    def list_content(self) -> List[Content]:
        return self.db.query(Content).filter(Content.owner_id == self.user.id).all()

    def prepare_content_encryption(self, content: Content):
        (pub, priv) = rsa.newkeys(512)
        secret_data = priv.save_pkcs1()

        secret = Secret(
            data=secret_data
        )
        key = Key(
            kind="rsa",
            content=content,
            secret=secret
        )
        self.db.add(secret)
        self.db.add(key)
        self.db.commit()
