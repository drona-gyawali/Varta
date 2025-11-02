from typing import Generic, Type, TypeVar

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def create(self, obj_data: dict) -> ModelType:
        obj = self.model(**obj_data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get(self, id: str = None, email: EmailStr = None) -> ModelType | None:
        if id is None and email is None:
            return None

        query = select(self.model)
        if id is not None:
            query = query.where(self.model.id == id)
        elif email is not None:
            query = query.where(self.model.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_room_with_members(self, room_id: str):
        query = (
            select(self.model)
            .options(
                selectinload(self.model.members),
                selectinload(self.model.messages),
            )
            .where(self.model.id == room_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self, id: str = None) -> ModelType | None:
        if id is None:
            return None
        query = select(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update(self, id: str, obj_data: dict) -> ModelType | None:
        obj = await self.get(id)
        if not obj:
            return None
        for key, value in obj_data.items():
            setattr(obj, key, value)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: str) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True
