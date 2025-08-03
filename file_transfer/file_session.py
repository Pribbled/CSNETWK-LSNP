_sessions = {}

def register_session(file_id, data):
    """Register a file transfer session using the file ID."""
    _sessions[file_id] = data

def get_session(file_id):
    """Get the session data by file ID."""
    return _sessions.get(file_id)

def remove_session(file_id):
    """Remove a completed or cancelled file transfer session."""
    _sessions.pop(file_id, None)
