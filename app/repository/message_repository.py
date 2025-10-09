from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.core.logger import setup_logger
from app.models import message_model

logger = setup_logger("repository.message_repository")

class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    

    async def create_message(self, message:str):
        now = datetime.utcnow().replace(tzinfo=None)

        try:
            message = message_model.Messages(
                text=message,
                createdAt=now
            )

            self.db.add(message)
            await self.db.commit()
            await self.db.refresh(message)
            logger.info(f"Sucessfully stored data | storedAt={now}" )
            return message

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"DB Error on user creation | data={e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error on user creation| data={e}")
            raise
