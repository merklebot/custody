from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, LargeBinary, String, func
from sqlalchemy.orm import backref, relationship

from custody.db.base_class import Base


class Key(Base):
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True, index=True)

    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    content = relationship("Content", backref=backref("key", uselist=False))

    aes_key = Column(LargeBinary)

    kind = Column(String, nullable=False)
    secret_id = Column(Integer, ForeignKey("secrets.id"))
    secret = relationship("Secret")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class Secret(Base):
    __tablename__ = "secrets"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(LargeBinary, nullable=False)
