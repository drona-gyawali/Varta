from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.core.logger import setup_logger
from app.models import message_model
from app.repository.base_repository import BaseRepository

logger = setup_logger("repository.message_repository")


class MessageRepository(BaseRepository):
    def __init__(self, model, db):
        super().__init__(model, db)

    async def create_messages(self, text: str, user_id: str, room_id: str):
        try:
            message_data = await self.create(
                {
                    "text": text,
                    "user_id": user_id,
                    "room_id": room_id,
                }
            )

            return message_data

        except SQLAlchemyError as e:
            logger.error(f"Error Occured | fx = create_messages | error={e}")

        except Exception as e:
            logger.error(f"Error Occured | fx = create_messages | error={e}")

    async def get_messages(
        self, user_id: str, room_id: str | None = None, limit: int = 20, offset: int = 0
    ):
        try:
            query = select(self.model)

            if room_id:
                room_data = await self.db.execute(
                    select(message_model.Room)
                    .options(selectinload(message_model.Room.members))
                    .where(message_model.Room.id == room_id)
                )
                room = room_data.scalars().first()

                if not room:
                    return ValueError("Room does not exist")

                is_member = not room.is_private or any(
                    m.user_id == user_id for m in room.members
                )
                if not is_member:
                    return PermissionError("Access denied to this room")

                query = query.where(message_model.Message.room_id == room_id)

            query = (
                query.order_by(message_model.Message.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            count_query = select(func.count(message_model.Message.id))

            total_items = (await self.db.execute(count_query)).scalar()
            result = await self.db.execute(query)
            message = result.scalars().all()
            return message, total_items

        except Exception as e:
            logger.error(f"Error Occured | fx=get_messages | error={e}")
