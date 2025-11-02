from app.core.logger import setup_logger
from app.repository.message_repository import MessageRepository
from app.services.cache import cache

logger = setup_logger("message.message")


class MessageService:
    def __init__(self, model, db):
        self.message = MessageRepository(model, db)

    async def send_message(self, text: str, user_id: str, room_id: str = None):
        try:
            if not text.strip():
                logger.warning("fx=send_message | warning=Text cannot be empty")
                return ValueError("Message cannot be empty")

            data = await self.message.create_mesages(text, user_id, room_id)
            await cache.del_cache(f"room_data:{room_id}-{user_id}*")
            return data

        except Exception as e:
            logger.error(f"Error Occured | fx=send_message | error={e}")

    async def get_room_message(
        self, user_id: str, room_id: str | None = None, limit: int = 20, offset: int = 0
    ):
        try:
            if not user_id and not room_id:
                logger.warning(
                    "fx=get_room_message | warning=userid and room_id is not provided"
                )
                return ValueError("UserId and RoomId is expected")

            message, total_items = await self.message.get_messages(
                user_id, room_id, limit, offset
            )
            if message is None:
                return ValueError("Error occured while fetching messages")

            total_pages = (total_items + limit - 1) // limit

            return {
                "message": message,
                "pagination": {
                    "total_items": total_items,
                    "limit": limit,
                    "offset": offset,
                    "total_pages": total_pages,
                },
            }

        except Exception as e:
            logger.error(f"Error Occured | fx=get_room_message | error={e}")
