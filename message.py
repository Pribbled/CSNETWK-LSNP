def parse_message(data: str) -> dict:
    lines = data.strip().splitlines()
    msg = {}
    for line in lines:
        if ": " in line:
            key, val = line.split(": ", 1)
            msg[key.strip()] = val.strip()
    return msg

def build_message(fields: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n\n"
