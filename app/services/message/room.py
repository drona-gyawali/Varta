from app.core.logger import setup_logger
from app.repository.room_repository import RoomRepsitory
from app.schemas.message import PageMetadata, PaginationResponse, Room
from app.services.cache import cache

logger = setup_logger("message.room")


class RoomService:
    def __init__(self, model, db):
        self.room = RoomRepsitory(model, db)

    async def add_room(self, room_name: str, is_private: bool, user_id: str):
        """Create a room"""
        try:
            if not room_name.strip():
                logger.warning("Room name is Expected | fx=add_room")
                return ValueError("Room name is empty")

            if not isinstance(is_private, bool):
                logger.warning("is_private excepts boolean value | fx=add_room")
                return ValueError("Room name is empty")

            data = await self.room.create_room(room_name, is_private, user_id)
            await cache.del_cache(f"get_room:{user_id}*")
            return data

        except Exception as e:
            logger.error(f"Error Occured | fx=add_room | error={e}")

    async def delete_room(self, room_id: str, user_id: str):
        """Delete room by id"""
        try:
            if not room_id and not user_id:
                raise ValueError("fx parameter missing")

            deleted = await self.room.delete_room(room_id, user_id)
            if not deleted:
                raise Exception("Falied to delete room")

            await cache.del_cache(f"get_room:{user_id}*")
            return deleted

        except Exception as e:
            logger.error(f"Error Occured | fx=delete_room | error={e}")
            raise e
        except ValueError as ve:
            logger.error(f"Error Occured | fx=delete_room | error={ve}")
            raise ve
        except PermissionError as pe:
            logger.error(f"Error Occured | fx=delete_room | error={pe}")
            raise pe

    async def get_room(self, user_id: str, limit: int, offset: int):
        """List of the public and pivate room"""
        try:
            keys = f"get_room:{user_id}-{limit}-{offset}"
            cached = await cache.get_cache(keys)
            if cached:
                return {**cached, "cached": True}
            if not user_id:
                logger.warning("user id is Expected | fx=get_room")
                raise ValueError("user id  is empty")

            room, total_items = await self.room.get_users_rooms(user_id, limit, offset)

            if room is None:
                return ValueError("error occured while fetching room")

            total_pages = (total_items + limit - 1) // limit
            rooms = [
                Room(
                    id=r.id,
                    is_private=r.is_private,
                    owner=r.owner,
                    name=r.name,
                    created_at=r.created_at,
                )
                for r in room
            ]
            data = PaginationResponse(
                message=rooms,
                pagination=PageMetadata(
                    total_items=total_items,
                    limit=limit,
                    offset=offset,
                    total_pages=total_pages,
                ),
            )
            await cache.set_cache(keys, data)
            return data

        except Exception as e:
            logger.error(f"Error Occured | fx=get_room | error={e}")

    async def get_room_data(self, room_id: str, user_id: str, limit: int, offset: int):
        """Room data and its details"""
        try:
            if not room_id and not user_id:
                logger.warning("room id  and user id is Expected | fx=get_room_data")
                return ValueError("user id and room id is empty")
            key = f"room_data:{room_id}-{user_id}-{limit}-{offset}"
            cached = await cache.get_cache(key)
            if cached:
                return {**cached, "cached": True}
            data = await self.room.get_users_room_data(room_id, user_id, limit, offset)
            await cache.set_cache(key, data)
            return data

        except Exception as e:
            logger.error(f"Error Occured | fx=get_room_data | error={e}")

    async def join_room(
        self, room_id: str, user_id: str, invite_token: str | None = None
    ):
        """Join the room"""
        try:
            data = await self.room.join_room(room_id, user_id, invite_token)
            await cache.del_cache(f"get_room:{user_id}*")
            await cache.del_cache(f"list_room_members:{room_id}*")
            return data
        except Exception as e:
            logger.error(f"Error Occured | fx=join_room | error={e}")

    async def create_invitation_link(self, room_id, user_id):
        """create invitation link"""
        try:
            if not room_id and not user_id:
                return ValueError(
                    "Link creation needed room_id and user_id parameter filled"
                )

            data = await self.room.create_invite_link(room_id, user_id)
            return data

        except Exception as e:
            logger.info(f"Error Occured | fx=create_invitation_link | error={e} ")

    async def list_room_members(
        self, room_id: str, user_id: str, limit: int, offset: int
    ):
        try:
            if not room_id and not user_id:
                return ValueError(
                    "Room members list needed room_id and user_id parameter filled"
                )
            key = f"list_room_members:{room_id}-{user_id}"
            cached = await cache.get_cache(key)
            if cached:
                return {**cached, "cached": True}
            data = await self.room.get_room_members(room_id, user_id, limit, offset)
            await cache.set_cache(key, data)
            return data

        except Exception as e:
            logger.error(f"Error  Occured | fx=list-room_members | error={e}")

    async def validate_invite_token(self, room_id: str, user_id: str, token: str):
        try:
            if not room_id and not user_id and not token:
                return ValueError("Invalid Input occured in parameter")
            joined_room = await self.room.join_room(room_id, user_id, token)
            if not joined_room:
                return PermissionError("User is unauthorized to access the room")

            await cache.del_cache(f"get_room:{user_id}*")
            await cache.del_cache(f"list_room_members:{room_id}*")
            return joined_room
        except Exception as e:
            logger.error(f"Error  Occured | fx=validate_invite_token | error={e}")
