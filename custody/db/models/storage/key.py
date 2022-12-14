from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, LargeBinary, String, func
from sqlalchemy.orm import relationship

from custody.db.base_class import Base


class Key(Base):
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True, index=True)

    owner = relationship("User", back_populates="keys")
    owner_id = Column(Integer, ForeignKey("users.id"))

    aes_key = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    secret_id = Column(Integer, ForeignKey("secrets.id"))
    secret = relationship("Secret")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Secret(Base):
    __tablename__ = "secrets"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(LargeBinary, nullable=False)
