from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from custody.db.base_class import Base


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    original_cid = Column(String)
    name = Column(String)
    encrypted_cid = Column(String, nullable=True)
    original_size = Column(BigInteger, nullable=True)
    encrypted_size = Column(BigInteger, nullable=True)
    is_on_crust = Column(Boolean, nullable=True)
    owner = relationship("User", back_populates="content")
    owner_id = Column(Integer, ForeignKey("users.id"))

    status = Column(String, index=True)

    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
