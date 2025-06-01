from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import Mapped

from database.db import (Base)


class User(Base):

    username: Mapped[str] = Column(String, unique=True, index=True)
    password: Mapped[str] = Column(String)
    is_admin: Mapped[bool] = Column(Boolean, default=True)