import time

def create_token(user_id, ttl, scope):
    expiry = int(time.time()) + ttl
    return f"{user_id}|{expiry}|{scope}"

def validate_token(token, expected_scope):
    try:
        user_id, expiry, scope = token.split("|")
        return scope == expected_scope and int(expiry) >= int(time.time())
    except Exception:
        return False
