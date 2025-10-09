from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from app.services.auth import AuthService
from app.core.logger import setup_logger
from app.core.database import DbInstance
from app.models.auth_model import User
from app.auth.schemas.auth import UserCreation, ProfileDetails
from app.auth.dependencies import get_current_user

logger = setup_logger("api.v1.auth")

router = APIRouter(
    prefix="/api/v1",
    tags=["Auth"]
)

@router.post('/register')
async def register(data:UserCreation, db:AsyncSession = Depends(DbInstance.get_db)):
    try:
        service_init = AuthService(User, db)
        user_data = await service_init.register_service(data.email, data.password) 
        if not user_data:
            return {
                "failure":status.HTTP_400_BAD_REQUEST,
                "error": "missing user data",
            }
        
        
        return {
            "success": status.HTTP_201_CREATED,
            "messsage": "Registration was successful"
        }
    
    except Exception as e:
        logger.error(f"Registration failed | erro={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.post("/login")
async def login(formdata:OAuth2PasswordRequestForm = Depends(), db:AsyncSession = Depends(DbInstance.get_db)):
    try:
        service_init = AuthService(User, db)
        access_token = await  service_init.login_service(formdata.username, formdata.password)

        if not access_token:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "User unable to login",
            }
        
        response = JSONResponse(
            content = {
                "sucess": status.HTTP_200_OK,    
                "message": "Login Successful"
                }
            )
        logger.info("Login Sucessfull")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False, 
            samesite="lax",
        )

        return response
    
    except Exception as e:
        logger.error(f"login failed | erro={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )



@router.get("/profile_details", response_model=ProfileDetails)
async def profile_details(
    db: AsyncSession = Depends(DbInstance.get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service_init = AuthService(User, db)
        user_data = await service_init.profile_service(current_user.id)

        if not user_data:
            raise HTTPException (
                status_code =status.HTTP_400_BAD_REQUEST,
                detail="Error while fetching profile view"
            )

        return ProfileDetails(
            success=status.HTTP_200_OK,
            id=user_data.id,
            email=user_data.email,
            profileUrl=user_data.profile_img,
            createdAt=user_data.created_at,
        )

    except Exception as e:
        logger.error(f"Fetching profile failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
