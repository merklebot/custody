from sqlalchemy import TIMESTAMP, ForeignKey, BigInteger, Column, Integer, String, func

from custody.db.base_class import Base
from sqlalchemy.orm import relationship
from custody.db.models.storage.key import Key

class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    original_cid = Column(String)
    owner = relationship("User", back_populates="content")
    owner_id = Column(Integer, ForeignKey("users.id"))

    status = Column(String, index=True)

    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

