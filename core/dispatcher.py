from protocol import serializer
from protocol import message_types as mt

class Dispatcher:
    def __init__(self, peer):
        self.peer = peer

    def handle(self, raw_message, addr):
        msg = serializer.deserialize_message(raw_message)
        msg_type = msg.get("TYPE")

        if msg.get("FROM") == self.peer.user_id or msg.get("USER_ID") == self.peer.user_id:
            return

        if msg_type == mt.PROFILE:
            display = msg.get("DISPLAY_NAME", msg.get("USER_ID"))
            status = msg.get("STATUS", "")
            print(f"[PROFILE] {display}: {status}")

        elif msg_type == mt.POST:
            display = msg.get("USER_ID")
            content = msg.get("CONTENT", "")
            print(f"[POST] {display}: {content}")

        elif msg_type == mt.DM:
            from_user = msg.get("FROM")
            content = msg.get("CONTENT")
            print(f"[DM] {from_user}: {content}")

        elif msg_type == mt.FOLLOW:
            from_user = msg.get("FROM")
            print(f"User {from_user} has followed you")

        elif msg_type == mt.UNFOLLOW:
            from_user = msg.get("FROM")
            print(f"User {from_user} has unfollowed you")
