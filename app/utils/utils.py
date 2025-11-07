import msgpack
from fastapi_limiter import FastAPILimiter

from app.core.conf import STORJ_BUCKET_OBJECT_URL
from app.core.logger import setup_logger
from app.services.redis import redisInit

logger = setup_logger("utils.utils")


## TODO: Implement end to end support of encryted message
def ConvertToBinary(data):
    return msgpack.packb(data)


def HumanReadable(data):
    return msgpack.unpackb(data, raw=False)


def construct_url(key, bucket_name):
    return f"{STORJ_BUCKET_OBJECT_URL}{bucket_name}/{key}"


async def starter():
    await FastAPILimiter.init(redisInit.get_connection)
