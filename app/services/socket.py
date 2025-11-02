import asyncio
import json
from datetime import datetime
from http.cookies import SimpleCookie
from typing import Any

import socketio

from app.auth.token import _token
from app.core.conf import MULTI_INSTANCE, origins
from app.core.database import DbInstance
from app.core.logger import setup_logger
from app.models.auth_model import User
from app.models.message_model import Message
from app.repository.auth_repository import AuthRepository
from app.repository.message_repository import MessageRepository
from app.services.kafka import consumer, producer
from app.services.redis import redisInit

logger = setup_logger("services.socket")


class SocketService:
    def __init__(self):
        logger.debug("Socket Connection Established")
        self._io = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=origins)
        self.register_listeners()
        asyncio.create_task(redisInit._redisSubscriberInit(self._io))
        asyncio.create_task(
            consumer.ConsumerClient.start(
                lambda db: MessageRepository(Message, db), "create_messages"
            )
        )

    @property
    def get_io(self):
        return self._io

    def attachToServer(self, server_instance: Any):
        return socketio.ASGIApp(self._io, other_asgi_app=server_instance)

    def register_listeners(self):
        @self._io.event
        async def connect(sid, environ):
            if "HTTP_COOKIE" not in environ:
                logger.warning("No HTTP_COOKIE in environ")
                return False
            cookie = SimpleCookie()
            cookie.load(environ["HTTP_COOKIE"])
            if "access_token" not in cookie:
                logger.warning("No access_token in cookie")
                return False
            token = cookie["access_token"].value
            verified_user_id = _token.verify_token(token)
            if not verified_user_id:
                logger.warning("Invalid or missing user_id from token")
                return False

            service = await DbInstance.process_db_sockets(
                lambda db: AuthRepository(User, db),
                "profile_details",
                str(verified_user_id.id),
            )
            if not service:
                logger.warning(f"No user found for id={verified_user_id.id}")
                return False

            user_email = (
                service.get("email")
                if isinstance(service, dict)
                else getattr(service, "email", None)
            )
            user_img = (
                service.get("email")
                if isinstance(service, dict)
                else getattr(service, "profile_img", None)
            )

            if not user_email:
                logger.warning(f"No email found for user_id={verified_user_id.id}")
                return False

            await self._io.save_session(
                sid,
                {
                    "user_id": str(verified_user_id.id),
                    "user_email": user_email,
                    "user_profile": user_img,
                },
            )

            logger.info(
                f"Client connected: id={sid} | user_id={verified_user_id.id} | email={user_email}"
            )
            await self._io.emit("server message", {"msg": "welcome"}, to=sid)
            return True

        @self._io.event
        async def disconnect(sid):
            session = await self._io.get_session(sid)
            user_id = session.get("user_id")
            if not user_id:
                logger.warning(f"Disconnect: user_id not found for sid={sid}")
                return
            rooms = session.get("rooms", [])
            for room in rooms:
                await self._io.leave_room(sid, room)

            await self._io.emit("user_offline", {"user_id": user_id})
            logger.info(f"Client disconnected: id={sid} | user_id={user_id}")

        @self._io.on("join_room")
        async def join_room(sid, data):
            session = await self._io.get_session(sid)
            user_id = session.get("user_id")
            if not user_id:
                logger.warning(f"join_room: user_id not found for sid={sid}")
                return
            room_id = data.get("room_id")
            if not room_id:
                logger.warning(f"join_room: room_id not provided by sid={sid}")
                return
            if isinstance(room_id, str):
                room_id = [room_id]
            joined_rooms = session.get("rooms", [])
            for room in room_id:
                await self._io.enter_room(sid, room)
                if room not in joined_rooms:
                    joined_rooms.append(room)
                await self._io.emit("user_joined", {"user_id": user_id}, room=room)

            await self._io.save_session(
                sid,
                {
                    "user_id": user_id,
                    "user_email": session.get("user_email"),
                    "rooms": joined_rooms,
                },
            )
            logger.info(f"User {user_id} joined rooms: {room_id}")
            return {"status": "ok", "joined_rooms": joined_rooms}

        @self._io.on("leave_room")
        async def leave_room(sid, data):
            session = await self._io.get_session(sid)
            user_id = session.get("user_id")
            if not user_id:
                logger.warning(f"leave_room: user_id not found for sid={sid}")
                return
            room_id = data.get("room_id")
            if not room_id:
                logger.warning(f"leave_room: room_id not provided by sid={sid}")
                return
            if isinstance(room_id, str):
                room_id = [room_id]
            joined_rooms = session.get("rooms", [])
            for room in room_id:
                if room in joined_rooms:
                    await self._io.leave_room(sid, room)
                    joined_rooms.remove(room)
                    await self._io.emit("user_left", {"user_id": user_id}, room=room)

            await self._io.save_session(
                sid,
                {
                    "user_id": user_id,
                    "user_email": session.get("user_email"),
                    "rooms": joined_rooms,
                },
            )
            logger.info(f"User {user_id} left rooms: {room_id}")
            return {"status": "ok"}

        @self._io.on("chat_message")
        async def chatMessage(sid, data):
            logger.debug(f"fx=chatMessage | data={data}")
            session = await self._io.get_session(sid)
            user_id = session.get("user_id")
            email = session.get("user_email")
            profile_url = session.get("user_profile")
            if not user_id or not email:
                logger.warning(
                    f"Invalid session for sid={sid}: user_id={user_id}, email={email}"
                )
                return
            room_id = data.get("room_id")
            if not room_id:
                logger.warning(f"Invalid message from user_id={user_id}: no room_id")
                return
            message_payload = {
                "text": data.get("text"),
                "user_id": user_id,
                "email": email,
                "avatar": profile_url,
                "created_at": data.get("created_at") or datetime.utcnow().isoformat(),
            }

            if MULTI_INSTANCE:
                await redisInit.get_pub.publish("MESSAGE", json.dumps(message_payload))
                logger.info(f"Redis published message | data={message_payload}")
            else:
                await self._io.emit(
                    "chat_message", {"sid": sid, "msg": message_payload}, room=room_id
                )
                logger.debug("Local emit done")

            logger.info(
                f"Message Received | sid={sid}, user_id={user_id}, email={email}, room_id={room_id}"
            )
            await producer.ProduceClient.produce_message(json.dumps(data))
            logger.debug("Message Produced to Kafka broker")

        @self._io.on("typing")
        async def handle_typing(sid, data):
            room_id = data.get("room_id")
            user_id = data.get("user_id")
            await self._io.emit(
                "user_typing", {"user_id": user_id}, room=room_id, skip_sid=sid
            )

        @self._io.on("stop_typing")
        async def handle_stop_typing(sid, data):
            room_id = data.get("room_id")
            user_id = data.get("user_id")
            await self._io.emit(
                "user_stop_typing", {"user_id": user_id}, room=room_id, skip_sid=sid
            )


SocketInit = SocketService()
