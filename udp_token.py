import time
import hashlib

revoked_tokens = set()

def is_token_expired(token: str) -> bool:
    try:
        _, expiry, _ = token.split("|")
        return time.time() > int(expiry)
    except Exception:
        return True

def is_token_scope_valid(token: str, required_scope: str) -> bool:
    try:
        _, _, scope = token.split("|")
        return scope == required_scope
    except Exception:
        return False

def is_token_revoked(token: str) -> bool:
    return token in revoked_tokens

def validate_token(token: str, expected_scope: str) -> bool:
    return (
        not is_token_expired(token) and
        is_token_scope_valid(token, expected_scope) and
        not is_token_revoked(token)
    )

def revoke_token(token: str):
    revoked_tokens.add(token)

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
