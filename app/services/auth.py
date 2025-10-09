from pydantic import EmailStr
from app.repository.auth_repository  import AuthRepository
from app.auth.token import _token
from app.core.logger import setup_logger

logger = setup_logger("service.auth")


class AuthService:
    def __init__(self, model, db):
        self.auth = AuthRepository(model, db)

    async def register_service(self, email:EmailStr, password:str):
        try:
            existing_user = await self.auth.get(email)
            
            if(existing_user):
                return ValueError("User email already exists")

            hash_password = _token.hash_password(str(password))
            new_user = await self.auth.create_user(email, hash_password)
            logger.info(f"User Created Successfully | data={email}")
            return new_user

        except Exception as e:
            logger.error(f"Error occured | fx=register | error={e}")
    
    #TODO: fastapi form attributes is by default set to username, However assume username == email in route
    async def login_service(self, email: EmailStr, password: str):
        try:
            user_data = await self.auth.get(email)
            
            if not user_data:
                logger.error(f"Error occured | fx=login | error=user not found")
                raise PermissionError("Wrong credential passed")

            try:
                verify_password = _token.verify_password(password, user_data.password)
            except Exception as e:
                logger.error(f"Error occured | fx=login | error=invalid password hash | {e}")
                raise PermissionError("Wrong credential passed")
            
            if not verify_password:
                logger.error(f"Error occured | fx=login | error=wrong credentials")
                raise PermissionError("Wrong credential passed")
            
            access_token = _token.create_access_token(user_id=user_data.id)
            return access_token

        except Exception as e:
            logger.error(f"Error occured | fx=login | error={e}")
            return None
        
    async def profile_service(self, id:str):
        try:
            if not id:
                logger.error(f'id is missing | fx=profile_service')
                raise ValueError("Id is missing")
            try:            
                user_data = await self.auth.get_all(id=id)
            except Exception as e:
                logger.error(f"Error Occured | fx=profile_service | error={e}")
                raise ValueError(f"Database Error | error={e}")
            
            return user_data
        
        except Exception as e:
            logger.error(f"Error | fx=profile_service | error={e}")




