from collections import defaultdict
from time import time
import uuid
import socket
# Generate a unique user ID at startup
USER_ID = str(uuid.uuid4())[:8]  # or use a different scheme if LSNP requires a different format

# Optional: get local IP for better identification
LOCAL_IP = socket.gethostbyname(socket.gethostname())

config = {
    "USER_ID": USER_ID,
    "LOCAL_IP": LOCAL_IP,
    # Add more as needed (like display name, etc.)
}


local_profile = {
    "Name": "",
    "Handle": "",
    "Bio": "",
    "Avatar": "",
}

# Known peers and profiles
peers = {}  # USER_ID → {DISPLAY_NAME, STATUS, AVATAR, etc.
posts = {}  # {POST_ID: message}
tokens = {}  # {token_string: {"EXPIRES_AT": 1234567890, "SCOPE": "DM,..."}}
revoked_tokens = set()
dm_history = []
follow_map = defaultdict(set)  # USER_ID → set of followers
group_map = defaultdict(dict)  # GROUP_ID → {group_name, members}
# revoked = set()
seen_message_ids = set()
file_transfers = {}  # FILEID → chunks
groups = {}  # {group_id: {"members": set(USER_IDs)}}
games = {}  # GAMEID → current board state
