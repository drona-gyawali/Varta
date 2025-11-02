import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.logger import setup_logger
from app.models import message_model
from app.repository.base_repository import BaseRepository
from app.schemas.message import (
    MessageResponse,
    PageMetadata,
    RoomMemberModel,
    RoomMemberResponse,
    RoomResponseModel,
    UserRoomResponse,
)

logger = setup_logger("repository.room_repository")


class RoomRepsitory(BaseRepository):
    def __init__(self, model, db):
        super().__init__(model, db)

    async def create_room(self, room_name: str, is_private: bool, user_id: str):
        try:
            room_data = await self.create(
                {"name": room_name, "is_private": is_private, "owner": str(user_id)}
            )

            creator_member = message_model.RoomMember(
                room_id=room_data.id, user_id=user_id
            )
            self.db.add(creator_member)
            await self.db.commit()
            await self.db.refresh(creator_member)

            return room_data

        except SQLAlchemyError as e:
            logger.error(f"Error Occured | fx = create_room | error={e}")

        except Exception as e:
            logger.error(f"Error Occured | fx = create_room | error={e}")

    async def delete_room(self, room_id: str, user_id: str):
        """Delete room by id"""
        try:
            if not room_id:
                logger.warning("Room Id is expected | fx=delete_room")
                raise ValueError("Room ID missing")

            if not user_id:
                logger.warning("User Id is missing")
                raise ValueError("User Id is missing")

            room = await self.get(id=room_id)

            if not room:
                logger.warning("No room with that id")
                raise ValueError("Room Id invalid")

            if room.owner != str(user_id):
                logger.warning("Unauthorized to delete room")
                raise PermissionError("Only room creator can delete room")

            deleted = await self.delete(room_id)
            return deleted

        except Exception as e:
            logger.error(f"Error Occured | fx=delete_room | error={e}")
            raise e

    async def get_users_rooms(self, user_id: str, limit: int = 20, offset: int = 0):
        try:
            query = (
                select(message_model.Room)
                .where(
                    or_(
                        message_model.Room.members.any(
                            message_model.RoomMember.user_id == user_id
                        )
                    )
                )
                .limit(limit)
                .offset(offset)
            )
            result = await self.db.execute(query)
            rooms = result.scalars().all()

            count_query = select(func.count(message_model.Room.id)).where(
                or_(
                    message_model.Room.members.any(
                        message_model.RoomMember.user_id == user_id
                    )
                )
            )
            total_items = (await self.db.execute(count_query)).scalar()

            return rooms, total_items

        except Exception as e:
            logger.error(f"Error Occurred | fx=get_users_rooms | error={e}")
            raise

        except SQLAlchemyError as e:
            logger.error(f"Error Occured | fx = get_users_room | error={e}")

        except Exception as e:
            logger.error(f"Error Occured | fx = get_users_room | error={e}")

    async def get_users_room_data(
        self,
        room_id: str,
        user_id: str,
        message_limit: int = 20,
        message_offset: int = 0,
    ):
        try:
            room_data = await self.get_room_with_members(room_id)
            if not room_data:
                logger.warning(
                    "Warning | fx=get_users_room_data | warning=room does not have data"
                )
                return None

            # Check access if room is private
            if room_data.is_private:
                is_member = any(
                    member.user_id == user_id for member in room_data.members
                )
                if not is_member:
                    raise PermissionError("Forbidden User")

            if room_data.messages:
                sorted_messages = sorted(room_data.messages, key=lambda m: m.created_at)
                total_messages = len(sorted_messages)
                paginated_messages = sorted_messages[
                    message_offset : message_offset + message_limit
                ]
                total_pages = (total_messages + message_limit - 1) // message_limit
            else:
                paginated_messages = []
                total_messages = 0
                total_pages = 0

            data = UserRoomResponse(
                room=RoomResponseModel(
                    id=room_data.id,
                    is_private=room_data.is_private,
                    owner=room_data.owner,
                    name=room_data.name,
                ),
                messages=[
                    MessageResponse(
                        id=m.id, text=m.text, created_at=m.created_at, user_id=m.user_id
                    )
                    for m in paginated_messages
                ],
                pagination=PageMetadata(
                    total_items=total_messages,
                    limit=message_limit,
                    offset=message_offset,
                    total_pages=total_pages,
                ),
            )

            return data

        except Exception as e:
            logger.error(f"Error Occurred | fx=get_users_room_data | error={e}")
            raise

    async def join_room(
        self, room_id: str, user_id: str, invite_token: str | None = None
    ):
        try:

            room_data = await self.get_room_with_members(room_id)

            if not room_data:
                logger.warning("Warning | fx=join_room | Room not found")
                raise ValueError("Room not found")

            if any(member.user_id == user_id for member in room_data.members):
                logger.info("User already in the room")
                return room_data

            if room_data.is_private:
                if not invite_token or not await self.validate_invite_link(
                    user_id, room_data.id, invite_token
                ):
                    raise PermissionError("Request Forbidden")

            new_member = message_model.RoomMember(
                room_id=room_data.id,
                user_id=user_id,
            )
            self.db.add(new_member)
            await self.db.commit()
            await self.db.refresh(new_member)
            return room_data

        except PermissionError as e:
            logger.error(f"Error Occurred | fx=join_room | error={e}")
        except SQLAlchemyError as e:
            logger.error(f"Error Occurred | fx=join_room | error={e}")
        except Exception as e:
            logger.error(f"Error Occurred | fx=join_room | error={e}")

    # TODO: Personal acknowledgement: as this logic is not secure because problems like
    # spam invite, can occured and I have just allowed at least for now.
    # this is reminder for me to rewrite this logic to support expire, and flags in future
    async def create_invite_link(self, room_id: str, user_id: str):
        try:

            room_data = await self.get_room_with_members(room_id)
            if not room_data:
                raise ValueError("Room does not exist")

            is_member = any(member.user_id == user_id for member in room_data.members)
            if not is_member:
                raise PermissionError("Only members can create invite links")

            if not room_data.is_private:
                raise PermissionError("Public rooms don't need invite links")

            token = str(uuid.uuid4())
            invite_link = message_model.RoomInvite(
                room_id=room_data.id, invite_token=token
            )

            self.db.add(invite_link)
            await self.db.commit()
            await self.db.refresh(invite_link)
            return invite_link

        except SQLAlchemyError as e:
            logger.error(f"Error Occurred | fx=create_invite_link | error={e}")
        except Exception as e:
            logger.error(f"Error Occurred | fx=create_invite_link | error={e}")

    async def validate_invite_link(self, user_id: str, room_id: str, invite_token: str):
        try:

            room_data = await self.get_all(room_id)

            if not room_data:
                return ValueError("Room does not exist")

            is_member = any(member.user_id == user_id for member in room_data.members)
            if is_member:
                logger.info(" fx=validate_invite_link | User is already a member")
                return True

            query = select(message_model.RoomInvite).where(
                and_(
                    message_model.RoomInvite.invite_token == invite_token,
                    message_model.RoomInvite.room_id == room_id,
                )
            )
            result = await self.db.execute(query)
            validate_data = result.scalars().first()
            return True if validate_data else False

        except SQLAlchemyError as e:
            logger.error(f"Error Occurred | fx=validate_invite_link | error={e}")

        except Exception as e:
            logger.error(f"Error Occurred | fx=validate_invite_link | error={e}")

    async def get_room_members(
        self, room_id: str, user_id: str, limit: int = 20, offset: int = 0
    ):
        try:
            member_check = await self.db.execute(
                select(message_model.RoomMember).where(
                    message_model.RoomMember.room_id == room_id,
                    message_model.RoomMember.user_id == user_id,
                )
            )
            if not member_check.scalars().first():
                raise PermissionError("You are not a member of this room")

            query = (
                select(message_model.RoomMember)
                .where(message_model.RoomMember.room_id == room_id)
                .limit(limit)
                .offset(offset)
            )

            result = await self.db.execute(query)
            members = result.scalars().all()

            # Count total members
            total_items = (
                await self.db.execute(
                    select(func.count(message_model.RoomMember.id)).where(
                        message_model.RoomMember.room_id == room_id
                    )
                )
            ).scalar()

            total_pages = (total_items + limit - 1) // limit if total_items else 0
            data = RoomMemberResponse(
                members=[
                    RoomMemberModel(
                        user_id=m.user_id,
                        joined_at=m.joined_at,
                    )
                    for m in members
                ],
                pagination=PageMetadata(
                    total_items=total_items,
                    limit=limit,
                    offset=offset,
                    total_pages=total_pages,
                ),
            )
            return data
        except Exception as e:
            logger.error(f"Error Occurred | fx=get_room_members_db | error={e}")
            raise
