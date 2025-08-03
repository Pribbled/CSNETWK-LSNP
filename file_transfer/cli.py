import os
from file_transfer.sender import send_file_offer, send_file_chunks

def file_transfer_cli():
    to_user_id = input("Enter recipient USER_ID: ").strip()
    file_path = input("Enter file path: ").strip()
    description = input("Enter file description (optional): ").strip()

    file_id = send_file_offer(to_user_id, file_path, description)
    if file_id:
        send_file_chunks(to_user_id, file_path, file_id)
