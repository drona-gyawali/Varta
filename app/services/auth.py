from datetime import timedelta
from functools import lru_cache

from fastapi import HTTPException
from pydantic import EmailStr

from app.auth.schemas.auth import ProfileDetails
from app.auth.token import _token
from app.core.logger import setup_logger
from app.repository.auth_repository import AuthRepository
from app.services.cache import cache

logger = setup_logger("service.auth")


class AuthService:
    def __init__(self, model, db):
        self.auth = AuthRepository(model, db)

    async def register_service(self, email: EmailStr, password: str):
        try:
            logger.debug(f"fx=register_service, payload email={email}, password=******")
            existing_user = await self.auth.get(email=email)
            if existing_user:
                raise ValueError("User email already exists")

            hash_password = _token.hash_password(str(password))
            new_user = await self.auth.create_user(email, hash_password)
            logger.info(f"User Created Successfully | data={email}")
            return new_user

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Error occured | fx=register | error={e}")

    # TODO: fastapi form attributes is by default set to username, However assume username == email in route
    async def login_service(self, email: EmailStr, password: str):
        try:
            user_data = await self.auth.get(email=email)
            logger.debug(f"fx=login_service| data={user_data.email}")
            if not user_data:
                logger.error("Error occured | fx=login | error=user not found")
                raise PermissionError("Wrong credential passed")

            try:
                verify_password = _token.verify_password(password, user_data.password)
            except Exception as e:
                logger.error(
                    f"Error occured | fx=login | error=invalid password hash | {e}"
                )
                raise PermissionError("Wrong credential passed")

            if not verify_password:
                logger.error("Error occured | fx=login | error=wrong credentials")
                raise PermissionError("Wrong credential passed")

            access_token = _token.create_access_token(user_id=user_data.id)
            refresh_token = _token.create_access_token(
                user_id=user_data.id, expires_delta=timedelta(days=7)
            )
            return {"access_token": access_token, "refresh_token": refresh_token}

        except Exception as e:
            logger.error(f"Error occured | fx=login | error={e}")
            return None

    @lru_cache(maxsize=500)
    async def profile_service(self, id: str):
        try:
            if not id:
                logger.error("id is missing | fx=profile_service")
                raise ValueError("Id is missing")
            try:
                key = f"user_profile:{id}"
                cached = await cache.get_cache(key)
                if cached:
                    return {**cached, "cached": True}
                user_data = await self.auth.get_all(id=id)

                data = ProfileDetails(
                    id=user_data.id,
                    email=user_data.email,
                    profileUrl=user_data.profile_img,
                    createdAt=user_data.created_at,
                )
            except Exception as e:
                logger.error(f"Error Occured | fx=profile_service | error={e}")
                raise ValueError(f"Database Error | error={e}")

            await cache.set_cache(key, data)
            return data

        except Exception as e:
            logger.error(f"Error | fx=profile_service | error={e}")

    async def update_profile(self, id, obj_data):
        try:
            updated_content = await self.auth.update(id, obj_data)
            return updated_content
        except Exception as e:
            logger.error(f"Error Occured | fx=update_profile | error={e}")
            raise ValueError(f"Database Error | error={e}")
