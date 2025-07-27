from .message_types import MESSAGE_TERMINATOR, SEPARATOR

def serialize_message(message_dict):
    lines = [f"{key}{SEPARATOR}{value}" for key, value in message_dict.items()]
    return "\n".join(lines) + MESSAGE_TERMINATOR

def deserialize_message(raw):
    lines = raw.strip().split("\n")
    msg = {}
    for line in lines:
        if SEPARATOR in line:
            key, val = line.split(SEPARATOR, 1)
            msg[key.strip()] = val.strip()
    return msg
