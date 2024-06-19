def read_byte(file):
    return int.from_bytes(file.read(1), "little")


def read_short(file):
    return int.from_bytes(file.read(2), "little")


def read_integer(file):
    return int.from_bytes(file.read(4), "little")


def read_long(file):
    return int.from_bytes(file.read(8), "little")


def read_uleb128(file):
    result, shift = 0, 0
    while True:
        byte = read_byte(file)
        result |= (byte & 0x7f) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return result


def read_string(file):
    first_byte = read_byte(file)
    if first_byte == 0x00:
        return ""
    elif first_byte != 0x0b:
        return ""

    length = read_uleb128(file)

    ret_val = file.read(length)

    return ret_val.decode("utf-8")
    

def read_custom(file, length):
    return file.read(length)
