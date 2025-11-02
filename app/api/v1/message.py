from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import DbInstance
from app.core.logger import setup_logger
from app.models.auth_model import User
from app.models.message_model import Message, Room
from app.schemas import message
from app.services.message.message import MessageService
from app.services.message.room import RoomService

logger = setup_logger("api.v1.message")

router = APIRouter(prefix="/api/v1", tags=["Message"])


# -----------------------------
# Create Room
# -----------------------------
@router.post("/create-rooms", status_code=status.HTTP_201_CREATED)
async def create_room(
    data: message.CreateLink,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """Create a room to chat"""
    try:
        user_id = current_user.id
        if not user_id:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "Unauthorized access forbidden",
            }

        service = RoomService(Room, db)
        response = await service.add_room(data.room_name, data.is_private, user_id)

        if not response:
            return {
                "failure": status.HTTP_400_BAD_REQUEST,
                "msg": "Error occurred while creating room",
            }

        return {"success": status.HTTP_201_CREATED, "msg": "Room created successfully"}

    except Exception as e:
        logger.error(f"Room creation failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# Get All Rooms
# -----------------------------
@router.get("/rooms", status_code=status.HTTP_200_OK)
async def get_rooms(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """List of rooms accessible to the user"""
    try:
        user_id = current_user.id
        print(user_id)
        if not user_id:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "Unauthorized access",
            }

        service = RoomService(Room, db)
        response = await service.get_room(user_id, limit, offset)

        if not response:
            return {
                "failure": status.HTTP_400_BAD_REQUEST,
                "msg": "No rooms found or error occurred while fetching",
            }

        return {"success": status.HTTP_200_OK, "data": response}

    except Exception as e:
        logger.error(f"get_rooms failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# Get Room Details
# -----------------------------
@router.get("/rooms/{id}", status_code=status.HTTP_200_OK)
async def get_room_details(
    id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """Get details of a private room and its members"""
    try:
        user_id = current_user.id
        service = RoomService(Room, db)
        response = await service.get_room_data(id, user_id, limit, offset)
        return {"success": status.HTTP_200_OK, "room_data": response}

    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden User")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error Occurred | fx=get_private_room_details | error={e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# -----------------------------
# Delete Room
# -----------------------------
@router.delete("/rooms/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """Delete Rooms of user by room_id"""
    try:
        user_id = current_user.id
        service = RoomService(Room, db)
        response = await service.delete_room(id, user_id)
        if response:
            return {
                "success": status.HTTP_204_NO_CONTENT,
            }
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden User")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error Occurred | fx=get_private_room_details | error={e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# -----------------------------
# Join Room
# -----------------------------
@router.post("/rooms/{id}/join", status_code=status.HTTP_200_OK)
async def join_room(
    id: str,
    data: message.JoinRoom,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """Join a room using an invite token"""
    try:
        user_id = current_user.id
        if not user_id:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "Unauthorized access",
            }

        service = RoomService(Room, db)
        response = await service.join_room(id, user_id, data.invite_token)

        if not response:
            return {
                "failure": status.HTTP_400_BAD_REQUEST,
                "msg": "Error occurred while joining room",
            }

        return {"success": status.HTTP_200_OK, "msg": "User successfully joined room"}

    except PermissionError as pe:
        logger.error(f"Error Occurred | fx=join_room | error={pe}")
        raise HTTPException(status_code=400, detail=str(pe))

    except ValueError as ve:
        logger.error(f"Error Occurred | fx=join_room | error={ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"Error Occurred | fx=join_room | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# Create Invitation Link
# -----------------------------
@router.post("/rooms/{id}/invite", status_code=status.HTTP_200_OK)
async def create_invitation_link(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """Generate an invitation token for a private room"""
    try:
        user_id = current_user.id
        service = RoomService(Room, db)
        response = await service.create_invitation_link(id, user_id)
        return {
            "status": status.HTTP_200_OK if response else status.HTTP_400_BAD_REQUEST,
            "invitation_token": (
                response.invite_token if response else "Public room cannot create token"
            ),
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden User")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error Occurred | fx=create_invitation_link | error={e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# -----------------------------
# Get Room Members
# -----------------------------
@router.get("/rooms/{id}/members", status_code=status.HTTP_200_OK)
async def get_all_members(
    id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """List all members in a room"""
    try:
        user_id = current_user.id
        if not user_id:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "Unauthorized access",
            }

        service = RoomService(Room, db)
        response = await service.list_room_members(id, user_id, limit, offset)

        if not response:
            return {
                "failure": status.HTTP_400_BAD_REQUEST,
                "msg": "Error occurred while fetching member data",
            }

        return {"success": status.HTTP_200_OK, "data": response}

    except Exception as e:
        logger.error(f"Error Occurred | fx=get_all_members | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -----------------------------
# Get Messages
# -----------------------------
@router.get("/room/messages/", status_code=status.HTTP_200_OK)
async def get_room_messages(
    room_id: Optional[str] = Query(None, description="Filter messages by room ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """Fetch messages for a specific room, with pagination support"""
    try:
        user_id = current_user.id
        if not user_id:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "Unauthorized access",
            }

        service = MessageService(Message, db)
        messages = await service.get_room_message(
            user_id=user_id, room_id=room_id, limit=limit, offset=offset
        )

        if messages is None:
            return {
                "failure": status.HTTP_400_BAD_REQUEST,
                "msg": "Error occurred while fetching messages",
            }

        return {"success": status.HTTP_200_OK, "messages": messages}

    except Exception as e:
        logger.error(f"Error Occurred | fx=get_room_messages | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.post("/room/create-message", status_code=status.HTTP_201_CREATED)
async def create_message(
    data: message.MessageCreation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """Create user message"""
    try:
        user_id = current_user.id
        if not user_id:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "Unauthorized access",
            }

        service = MessageService(Message, db)
        new_message = await service.send_message(data.text, user_id, data.room_id)
        if not new_message:
            return {
                "failure": status.HTTP_400_BAD_REQUEST,
                "msg": "Error occurred while creating  message",
            }

        return {
            "success": status.HTTP_201_CREATED,
            "msg": "message created sucessfully",
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# ------------------------------------------------------
# Validate the token and  give room access
# : similar endpoint:/rooms/{id}/join -> manual
# new endpoint -> automatic access to the room
# -------------------------------------------------------
@router.post("/room/{room_id}/access/{token}", status_code=status.HTTP_200_OK)
async def access_private_rooms(
    room_id: str,
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(DbInstance.get_db),
):
    """Automatic join the room"""
    try:
        user_id = current_user.id
        if not user_id:
            return {
                "failure": status.HTTP_401_UNAUTHORIZED,
                "msg": "Unauthorized access",
            }

        service = RoomService(Room, db)
        joined_room = await service.validate_invite_token(room_id, user_id, token)
        if not joined_room:
            return {
                "failure": status.HTTP_400_BAD_REQUEST,
                "msg": "Error occurred while joining the room",
            }

        return {"success": status.HTTP_200_OK, "msg": "Room joined sucessfully"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
