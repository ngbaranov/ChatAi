from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from database.db import (Base)



class ChatHistory(Base):

    message: Mapped[str] = Column(String)
    role: Mapped[str] = Column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    session_id: Mapped[str] = mapped_column(String, default=lambda: uuid4().hex)

    user = relationship("User", back_populates="chat_history")
