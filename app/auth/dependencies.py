from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_model import User
from app.auth.token import  _token
from app.core.database import DbInstance
from app.repository.auth_repository import AuthRepository
from app.core.logger import setup_logger

logger = setup_logger("auth.dependencies")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(DbInstance.get_db)
):
    token = request.cookies.get("access_token")

    if not token:
        logger.error("No access token found in cookies")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token_data = _token.verify_token(str(token))
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    repository = AuthRepository(User, db)
    user = await repository.get(id=token_data.id)

    if not user:
        logger.error(f"User not found with ID: {token_data.user_id}")
        raise HTTPException(status_code=401, detail="User not found")

    return user
