from collections import defaultdict
from time import time

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
file_transfers = {}  # FILEID → chunks
groups = {}  # {group_id: {"members": set(USER_IDs)}}
games = {}  # GAMEID → current board state
