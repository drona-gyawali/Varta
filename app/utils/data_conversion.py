import msgpack

from app.core.logger import setup_logger

logger = setup_logger("utils.data_conversion")


## TODO: Implement end to end support of encryted message
def ConvertToBinary(data):
    return msgpack.packb(data)


def HumanReadable(data):
    return msgpack.unpackb(data, raw=False)
