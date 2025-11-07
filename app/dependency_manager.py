from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import DbInstance


class PublicDeps:
    def __init__(self, db: AsyncSession = Depends(DbInstance.get_db)):
        self.db = db


class PrivateDeps(PublicDeps):
    def __init__(
        self, current_user=Depends(get_current_user), db=Depends(DbInstance.get_db)
    ):
        super().__init__(db)
        self.user = current_user
