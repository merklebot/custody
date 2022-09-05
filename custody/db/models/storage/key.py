from sqlalchemy import TIMESTAMP, ForeignKey, BigInteger, Column, Integer, String, LargeBinary, func

from custody.db.base_class import Base
from sqlalchemy.orm import relationship, backref


class Key(Base):
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True, index=True)

    content_id = Column(Integer, ForeignKey('content.id'), nullable=False)
    content = relationship("Content", backref=backref("key", uselist=False))

    kind = Column(String, nullable=False)
    secret_id = Column(Integer, ForeignKey('secrets.id'))
    secret = relationship("Secret")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class Secret(Base):
    __tablename__ = "secrets"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(LargeBinary, nullable=False)

