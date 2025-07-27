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

        elif msg_type == mt.FILE_OFFER:
            from_user = msg.get("FROM")
            filename = msg.get("FILENAME")
            print(f"User {from_user.split('@')[0]} is sending you a file: {filename}. Do you accept?")

        elif msg_type == mt.FILE_CHUNK:
            file_id = msg.get("FILEID")
            chunk_index = int(msg.get("CHUNK_INDEX", -1))
            total_chunks = int(msg.get("TOTAL_CHUNKS", -1))
            data = msg.get("DATA", "")

            # Simple temporary in-memory storage
            self.peer.file_chunks.setdefault(file_id, {})[chunk_index] = data

            # If all chunks received
            if len(self.peer.file_chunks[file_id]) == total_chunks:
                chunks = [self.peer.file_chunks[file_id][i] for i in range(total_chunks)]
                file_data = "".join(chunks)  # Base64 str
                print("File transfer is complete.")

                # Optional: Notify sender
                msg = {
                    "TYPE": mt.FILE_RECEIVED,
                    "FROM": self.peer.user_id,
                    "TO": msg.get("FROM"),
                    "FILEID": file_id,
                    "STATUS": "COMPLETE",
                    "TIMESTAMP": int(time.time())
                }
                self.peer.udp.send(serializer.serialize_message(msg), addr=msg["TO"].split("@")[-1])

        elif msg_type == mt.FILE_RECEIVED:
            # Silent acknowledgment
            pass
