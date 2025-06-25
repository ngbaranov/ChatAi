from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import Mapped, relationship

from database.db import (Base)


class User(Base):

    username: Mapped[str] = Column(String, unique=True, index=True)
    password: Mapped[str] = Column(String)
    is_admin: Mapped[bool] = Column(Boolean, default=True)

    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")