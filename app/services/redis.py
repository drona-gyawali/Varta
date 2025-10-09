from redis.asyncio import Redis
from app.core.conf import REDISCONF
from app.core.logger import setup_logger

logger = setup_logger("service.redis")

class RedisService: 
    def __init__(self):
        self._publisher = Redis(
            host=REDISCONF.get("redisHost"),
            port=int(REDISCONF.get("redisPort")),
            password=REDISCONF.get("redisPassword"),
            decode_responses=True,
        )

        self._subscriber = Redis(
            host=REDISCONF.get("redisHost"),
            port=int(REDISCONF.get("redisPort")),
            password=REDISCONF.get("redisPassword"),
            decode_responses=True,
        )
    
    @property
    def get_pub(self) -> Redis:
        """Return the publisher client"""
        return self._publisher
    
    @property
    def get_sub(self) -> Redis:
        """Return the subscriber client"""
        return self._subscriber


    async def _redisSubscriberInit(self, io_emit):
        sub = self.get_sub.pubsub()
        await sub.subscribe("MESSAGE")
        logger.debug("Subscribed to Redis Channel: MESSAGE")
        async for message in sub.listen():
            if message["type"] == "message":
                data = message["data"]
                logger.info(f"Message delivered by redis |  data={data}")
                await io_emit.emit("chat_message", {"id": "Server", "msg": data})


redisInit = RedisService()
