from state import revoked_tokens
from utils import hash_token

def handle_revoke(fields, verbose=False):
    token = fields["TOKEN"]
    revoked_tokens.add(hash_token(token))
    # No output per RFC
