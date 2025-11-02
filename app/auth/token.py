from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from app.core.conf import ALGORITHM, SECRETKEY, TOKENEXPIRY
from app.core.logger import setup_logger
from app.schemas.token import TokenData

logger = setup_logger("auth.jwt")


class Token:

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def create_access_token(self, user_id: str, expires_delta: timedelta | None = None):
        logger.debug(f"userid = {user_id} | delta={expires_delta}")
        if not isinstance(user_id, str):
            raise TypeError(f"user_id must be str, got {type(user_id)}")
        to_encode = {"sub": str(user_id)}
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=int(TOKENEXPIRY))
        to_encode.update({"exp": int(expire.timestamp())})
        encoded_jwt = jwt.encode(to_encode, SECRETKEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, SECRETKEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing user id (sub)",
                )
            return TokenData(id=str(user_id))
        except InvalidTokenError:
            logger.error(f"Error | error={InvalidTokenError}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    def hash_password(self, password: str):
        if not password:
            return False
        logger.debug(f"PASSWORD={password}")
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str | None) -> bool:
        if not hashed_password:
            return False
        logger.debug(f"PASSWORD={plain_password}")
        return self.pwd_context.verify(plain_password, hashed_password)


_token = Token()
