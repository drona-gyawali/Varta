from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.schemas.auth import ProfileDetails, UpdateProfileurl, UserCreation
from app.auth.token import _token
from app.core.logger import setup_logger
from app.core.ratelimiter import RateLimiters
from app.core.storage import bucket
from app.dependency_manager import PrivateDeps, PublicDeps
from app.models.auth_model import User
from app.services.auth import AuthService

logger = setup_logger("api.v1.auth")


router = APIRouter(
    prefix="/api/v1",
    tags=["Auth"],
    dependencies=[Depends(RateLimiters.global_limiter())],
)


# -----------------------------
# Register
# -----------------------------
@router.post("/register")
async def register(data: UserCreation, deps: PublicDeps = Depends()):
    try:
        service_init = AuthService(User, deps.db)
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
    formdata: OAuth2PasswordRequestForm = Depends(), deps: PublicDeps = Depends()
):
    try:
        logger.debug(f"login | data={formdata.username}")
        service_init = AuthService(User, deps.db)
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
@router.get(
    "/profile_details",
    dependencies=[Depends(RateLimiters.user_rate_limiter)],
    response_model=ProfileDetails,
)
async def profile_details(
    deps: PrivateDeps = Depends(),
):
    try:
        service_init = AuthService(User, deps.db)
        user_data = await service_init.profile_service(deps.user.id)

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
    deps: PublicDeps = Depends(),
):
    try:
        service_init = AuthService(User, deps.db)
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


@router.put(
    "/profile-update",
    dependencies=[Depends(RateLimiters.user_rate_limiter)],
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_profile(
    data: UpdateProfileurl,
    deps: PrivateDeps = Depends(),
):
    try:
        user_id = deps.user.id
        service_init = AuthService(User, deps.db)
        updated = await service_init.update_profile(
            user_id, {"profile_img": data.profileUrl}
        )
        return {"data": {"email": updated.email, "img": updated.profile_img}}
    except Exception as e:
        logger.error(f"updating profile failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# Upload img Content
# -----------------------------
@router.post(
    "/generate-upload-url/{filename}",
    dependencies=[Depends(RateLimiters.user_rate_limiter)],
)
def generate_upload_url(
    filename: str,
    deps: PrivateDeps = Depends(),
):
    if not filename:
        return {"message": "filename is required"}

    try:
        user_id = deps.user.id
        presigned_url, objects_url = bucket.create_presigned_url(user_id, filename)
        if not presigned_url and not objects_url:
            return {"message": "Unable to create a upload url"}
        return {
            "presigned_url": presigned_url,
            "object_url": objects_url,
        }

    except Exception as e:
        logger.error(f"creating url failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# Delete img content
# -----------------------------
@router.delete(
    "delete-objects/{key}",
    dependencies=[Depends(RateLimiters.user_rate_limiter)],
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_objects(
    key: str,
    deps: PrivateDeps = Depends(),
):
    user_id = deps.id
    if not user_id:
        return {"message": "unauthorized user"}
    try:
        deleted = bucket.delete_object(key)
        if not deleted:
            return {"messgae": "unable to delete a object"}
        return {}
    except Exception as e:
        logger.error(f"deleting objects failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
