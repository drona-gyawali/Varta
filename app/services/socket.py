from typing import Any
import socketio
from app.core.conf import  origins
from app.core.logger import setup_logger
from app.services.redis import redisInit
from app.repository.message_repository import MessageRepository
from app.core.database import DbInstance
from app.services.kafka import producer, consumer

import asyncio

logger = setup_logger("services.socket")
 

class SocketService: 
    def __init__(self):
        logger.debug("Socket Connection Established")
        self._io =   socketio.AsyncServer(async_mode = "asgi", cors_allowed_origins=origins)
        self.register_listeners()
        asyncio.create_task(redisInit._redisSubscriberInit(self._io))
        asyncio.create_task(consumer.ConsumerClient.start(MessageRepository,"create_message"))

    @property
    def get_io(self):return self._io
        
    def attachToServer(self, server_instance:Any):
        return socketio.ASGIApp(self._io,other_asgi_app=server_instance)
    
    def register_listeners(self):
        @self._io.event
        async def connect(sid, environ, auth=None):
            logger.info(f"Client connected: id={sid}")
            await self._io.emit("server message", {"msg": "welcome"}, to=sid)
        

        @self._io.event
        async def disconnect(sid):logger.info(f"Client disconnected: id={sid}")


        @self._io.on("chat_message")
        async def chatMessage(sid, data):
            logger.info(f"Message Received | id={sid}, data={data}")
            await redisInit.get_pub.publish("MESSAGE", data)
            await self._io.emit("chat_message", {"sid": sid, "msg": data})
            await producer.ProduceClient.produce_message(data)
            logger.debug("Message Produced to kafka broker")


SocketInit = SocketService()