import time

#for token generation, same format as in rfc
def generateToken(id, ttl, scope):
    expiry = int(time.time()) + ttl
    return f"{id} | {expiry} | {scope}"

#for validation of token, checks if token is not yet expired, if scope matches expected use, and if token is not yet revoked
def isTokenValid(token, scope, r = set()):
    try:
        uid, exp, s = token.split("|")
        if int(exp) < int(time.time()):
            return False
        
        if s != scope:
            return False
        
        if token in r:
            return False
        
        return True
    except:
        return False