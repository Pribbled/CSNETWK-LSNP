from collections import defaultdict
from time import time
import uuid
import socket
from utils import get_local_ip
# Generate a unique user ID at startup
# USER_ID = str(uuid.uuid4())[:8]  # or use a different scheme if LSNP requires a different format

# Optional: get local IP for better identification
# LOCAL_IP = socket.gethostbyname(socket.gethostname())

local_profile = {
    "USER_ID": "",
    "USERNAME": "",
    "LOCAL_IP": get_local_ip(),
    "Name": "",
    "Handle": "",
    "Status": "",
    "Avatar": "",
}

# Known peers and profiles
peers = {}  # USER_ID → {DISPLAY_NAME, STATUS, AVATAR, etc.
posts = {}  # {POST_ID: message}
liked_posts = set()  # Store TIMESTAMPs of liked posts
likes_received = {}

tokens = {}  # {token_string: {"EXPIRES_AT": 1234567890, "SCOPE": "DM,..."}}
revoked_tokens = set()
dm_history = []

follow_map = defaultdict(set)  # USER_ID → set of followers
group_map = defaultdict(dict)  # GROUP_ID → {group_name, members}

seen_message_ids = set()
file_transfers = {}  # FILEID → chunks
games = {}  # GAMEID → current board state

def get_peer_address(user_id):
    username = user_id.split("@")[0]
    # Search for peer with matching username
    for peer_id, info in peers.items():
        if peer_id.startswith(username + "@"):
            return info["ADDRESS"]
    return None