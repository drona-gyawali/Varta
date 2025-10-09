
from pydantic import EmailStr
from sqlalchemy.exc import SQLAlchemyError

from app.core.logger import  setup_logger
from app.repository.base_repository import BaseRepository


logger = setup_logger("repository.auth_repository")

class AuthRepository(BaseRepository):
    def __init__(self, model, db):
        super().__init__(model, db)

    async def get_user(self, email:EmailStr ):
        try:
            user = await self.get(email)
            return user
        
        except SQLAlchemyError as e:
            logger.error(f"Error | fx=get_user | error={str(e)}")


    async def create_user(self, email:EmailStr, password:str):
        try:
            new_user = await self.create({
                "email":email,
                "password": password,
            })

            return new_user
        
        except SQLAlchemyError as e:
            logger.error(f"Error | fx=create_user | error={str(e)}")

        except Exception as e:
            logger.error(f"Error | fx=create_user | error={str(e)}")
    

    async def profile_details(self, id:str):
        try:
            details = await self.get_all(id)
            return details
        
        except SQLAlchemyError as e:
            logger.error(f"Error | fx=profile_user | error={str(e)}")

        except Exception as e:
            logger.error(f"Error | fx=profile_user | error={str(e)}")

