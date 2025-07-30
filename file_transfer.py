import os
import time
import base64
from message_parsing import buildMessage
from token_mng import generateToken

temp_buffer = {}

#sends a file offer to the receiver
def sendFileOffer(send_id, rcv_id, path, peer):
    file_id = os.urandom(4).hex()
    size = os.path.getsize(path)
    name = os.path.basename(path)
    token = generateToken(send_id, 3600, "file")

    msg = buildMessage({
        "TYPE": "FILE_OFFER",
        "FROM": send_id,
        "TO": rcv_id,
        "FILENAME": name,
        "FILESIZE": size,
        "FILETYPE": "application/octet-stream",
        "FILEID": file_id,
        "DESCRIPTION": f"Sending {name}",
        "TIMESTAMP": int(time.time()),
        "TOKEN": token
    })
    print(f"Sending file offer to {rcv_id.split('@')[1]}")
    print("Message: \n " + msg)
    peer.sendToOne(msg, rcv_id.split("@")[1])
    return file_id

#this splits the file into chunks
def sendFileChunks(send_id, rcv_id, path, file_id, peer, chunk_size = 512):
    token = generateToken(send_id, 3600, "file")
    with open(path, "rb") as f:
        data = f.read()

    total = (len(data) + chunk_size - 1)

    for i in range(total):
        chunk = base64.b64encode(data[i * chunk_size : (i + 1) * chunk_size]).decode()
        msg = buildMessage({
            "TYPE": "FILE_CHUNK",
            "FROM": send_id,
            "TO": rcv_id,
            "FILEID": file_id,
            "CHUNK_INDEX": i,
            "TOTAL_CHUNKS": total,
            "CHUNK_SIZE": chunk_size,
            "DATA": chunk,
            "TOKEN": token
        })
        peer.sendToOne(msg, rcv_id.split('@')[1])
        time.sleep(0.05)

#prompts the user to accept or reject the file offer
def handleFileOffer(parsed_msg):
    file_id = parsed_msg["FILEID"]
    sender = parsed_msg["FROM"]
    filename = parsed_msg["FILENAME"]
    size = parsed_msg["FILESIZE"]

    print(f"\n File offer from {sender}: {filename}")
    accept = input("Do you accept the file? (y/n): ")
    
    if accept.lower() == "y":
        print("Accepted file offer. Waiting for chunks...")
        temp_buffer[file_id] = {"chunks": {}, "total": int(size)}
    else:
        print("Rejected file offer.")

#processes the file chunks it receives
def handleFileChunk(parsed_msg):
    file_id = parsed_msg["FILEID"]
    i = int(parsed_msg["CHUNK_INDEX"])
    total = int(parsed_msg["TOTAL_CHUNKS"])
    data = parsed_msg["DATA"]

    if file_id not in temp_buffer:
        temp_buffer[file_id] = {"chunks": {}, "total": total}
    
    temp_buffer[file_id]["chunks"][i] = data

    if len(temp_buffer[file_id]["chunks"]) == total:
        print("File received successfully.")
        with open(f"received_{file_id}.bin", "wb") as out:
            for x in range(total):
                out.write(base64.b64decode(temp_buffer[file_id]["chunks"][i]))
        print(f"File saved as: received_{file_id}.bin")
        del temp_buffer[file_id]