from protocol import serializer
from protocol import message_types as mt
from protocol import file_handling as file_h

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
            user_id = msg.get("USER_ID")
            self.peer.known_peers[user_id] = addr[0]
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
            to_user = msg.get("TO")
            filename = msg.get("FILENAME")
            file_id = msg.get("FILEID")

            if to_user != self.peer.user_id:
                return

            self.peer.pending_file_offers[file_id] = msg
            print(f"User {from_user.split('@')[0]} is sending you a file: {filename}. Do you accept?")
            self.peer.awaiting_file_offer = file_id

            if self.awaiting_file_offer:
                response = line.strip().lower()
                fileid = self.awaiting_file_offer
                offer = self.pending_file_offers.get(fileid)

                if not offer:
                    print("No matching file offer found.")
                    self.awaiting_file_offer = None
                    return

                from_user = offer["FROM"]

                if response in ("yes", "y"):
                    self.send_message({
                        "TYPE": "FILE_ACCEPT",
                        "FROM": self.user_id,
                        "TO": from_user,
                        "FILEID": fileid,
                    }, addr=from_user.split("@")[1])
                    file_h.accept_file(self, file_id)
                    print(f"Accepted file: {offer['FILENAME']}")
                    self.peer.accepted_file_ids.add(fileid)
                else:
                    self.send_message({
                        "TYPE": "FILE_REJECT",
                        "FROM": self.user_id,
                        "TO": from_user,
                        "FILEID": fileid,
                    }, addr=from_user.split("@")[1])
                    file_h.reject_file(self, file_id)
                    print(f"Rejected file: {offer['FILENAME']}")
                    self.peer.rejected_file_ids.add(fileid)

                self.awaiting_file_offer = None
                return

        # elif msg_type == mt.FILE_ACCEPT

        elif msg_type == "FILE_REJECT":
            fileid = msg.get["FILEID"]
            to_user = msg.get["TO"]
            if to_user == self.peer.user_id:
                print(f"Your file was rejected by {msg.get['FROM']}.")

        elif msg_type == mt.FILE_CHUNK:
            file_id = msg.get("FILEID")
            chunk_index = int(msg.get("CHUNK_INDEX", -1))
            total_chunks = int(msg.get("TOTAL_CHUNKS", -1))
            data = msg.get("DATA", "")

            # simple temporary in-memory storage
            self.peer.file_chunks.setdefault(file_id, {})[chunk_index] = data

            # if all chunks received
            if len(self.peer.file_chunks[file_id]) == total_chunks:
                print(f"[DEBUG] Received file chunk {chunk_index+1}/{total_chunks} for file {file_id}")
                chunks = [self.peer.file_chunks[file_id][i] for i in range(total_chunks)]
                file_data = "".join(chunks)  # Base64 str
                print("File transfer is complete.")

                # optional: notify sender
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
            # put an ack here
            pass
