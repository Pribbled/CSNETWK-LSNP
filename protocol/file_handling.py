import os
import base64
from collections import defaultdict

class FileHandler:
    def __init__(self, save_dir='downloads'):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

        # Keeps track of file chunk info by file ID
        self.file_chunks = defaultdict(lambda: {
            'chunks': {},
            'total': 0,
            'filename': '',
            'from': '',
            'filetype': '',
            'received_count': 0
        })

        # Tracks accepted or rejected file IDs
        self.accepted_files = set()
        self.rejected_files = set()

    def accept_file(self, fileid):
        self.accepted_files.add(fileid)

    def reject_file(self, fileid):
        self.rejected_files.add(fileid)

    def is_accepted(self, fileid):
        return fileid in self.accepted_files

    def is_rejected(self, fileid):
        return fileid in self.rejected_files

    def init_file_transfer(self, fileid, filename, total_chunks, sender, filetype):
        self.file_chunks[fileid].update({
            'filename': filename,
            'total': total_chunks,
            'from': sender,
            'filetype': filetype,
            'received_count': 0,
        })

    def save_chunk(self, fileid, chunk_index, data_b64):
        if self.is_rejected(fileid):
            return False

        chunk_data = base64.b64decode(data_b64)
        self.file_chunks[fileid]['chunks'][chunk_index] = chunk_data
        self.file_chunks[fileid]['received_count'] += 1

        return self.is_complete(fileid)

    def is_complete(self, fileid):
        info = self.file_chunks[fileid]
        return len(info['chunks']) == info['total']

    def write_file(self, fileid):
        info = self.file_chunks[fileid]
        filename = os.path.join(self.save_dir, info['filename'])

        with open(filename, 'wb') as f:
            for i in range(info['total']):
                f.write(info['chunks'][i])
        
        return filename
