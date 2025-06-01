from dao.base import BaseDAO
from auth.model import User


class UserDAO(BaseDAO):
    model = User