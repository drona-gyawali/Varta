from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas.auth import ProfileDetails, UserCreation
from app.auth.token import _token
from app.core.database import DbInstance
from app.core.logger import setup_logger
from app.models.auth_model import User
from app.services.auth import AuthService

logger = setup_logger("api.v1.auth")

router = APIRouter(prefix="/api/v1", tags=["Auth"])


# -----------------------------
# Register
# -----------------------------
@router.post("/register")
async def register(data: UserCreation, db: AsyncSession = Depends(DbInstance.get_db)):
    try:
        service_init = AuthService(User, db)
        user_data = await service_init.register_service(data.email, data.password)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": status.HTTP_400_BAD_REQUEST,
                    "msg": "User email already exists in the system",
                },
            )

        return {
            "success": status.HTTP_201_CREATED,
            "messsage": "Registration was successful",
        }

    except ValueError as ve:
        logger.warning(f"Registration failed | reason={ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


# -----------------------------
# Login
# -----------------------------
@router.post("/login")
async def login(
    formdata: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    try:
        logger.debug(f"login | data={formdata.username}")
        service_init = AuthService(User, db)
        tokens = await service_init.login_service(formdata.username, formdata.password)

        if not tokens:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "Wrong Credentilas has been passed",
            }

        response = JSONResponse(
            content={"success": status.HTTP_200_OK, "message": "Login Successful"}
        )
        logger.info("Login Sucessfull")
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="none",
        )
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="none",
        )

        return response

    except Exception as e:
        logger.error(f"login failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# Refresh Token
# -----------------------------
@router.get("/refresh")
async def refresh_token(response: Response, refresh_token: str):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        payload = _token.verify_token(refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = _token.create_access_token(str(payload.id))
        if not new_access_token:
            raise HTTPException(status_code=401, detail="Access token unverified")

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="none",
        )
        return {"success": 201, "access_token": new_access_token}
    except Exception as e:
        logger.error(f"Error Occured | fx=refresh_token | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# Profile details
# -----------------------------
@router.get("/profile_details", response_model=ProfileDetails)
async def profile_details(
    db: AsyncSession = Depends(DbInstance.get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service_init = AuthService(User, db)
        user_data = await service_init.profile_service(current_user.id)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error while fetching profile view",
            )
        return user_data

    except Exception as e:
        logger.error(f"Fetching profile failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# TODO: This api is created for special purpose in frontend but need to modify
# or delete in future : source dronarajgyawali@gmail.com
@router.get("/kyc/{user_id}", response_model=ProfileDetails)
async def Know_your_customer(
    user_id: str,
    db: AsyncSession = Depends(DbInstance.get_db),
):
    try:
        service_init = AuthService(User, db)
        user_data = await service_init.profile_service(user_id)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error while fetching profile view",
            )

        return user_data

    except Exception as e:
        logger.error(f"Fetching profile failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# logout
# -----------------------------
@router.post("/logout")
def logout(response: Response):
    try:
        response.delete_cookie(key="access_token", path="/")
        return {"message": "Logged out succesfully"}
    except Exception as e:
        logger.error(f"Fetching profile failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
