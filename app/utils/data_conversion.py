import msgpack


def ConvertToBinary(data):
    return msgpack.packb(data)

def HumanReadable(data):
    return msgpack.unpackb(data, raw=False)