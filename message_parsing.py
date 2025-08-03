#for converting dict into proper msg, added also \n\n in the end as said in the rfc
def buildMessage(fields: dict) -> str:
    msg_lines = []
    for key, value in fields.items():
        msg_lines.append(f"{key}: {value}")
    msg = "\n".join(msg_lines) + "\n\n"
    return msg

#parses raw string into dict
def parseMessage(msg: str) -> dict:
    lines = msg.strip().split("\n")
    parsed_msg = {}

    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            parsed_msg[key.strip()] = value.strip()
    
    return parsed_msg