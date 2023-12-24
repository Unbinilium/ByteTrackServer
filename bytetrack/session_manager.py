from threading import Lock

from bytetrack.tracker_wrapper import TrackerWrapper

class SessionManager:
    def __init__(self):
        self.sessions = dict()
        self.sessions_lock = Lock()

    def get_sessions(self):
        with self.sessions_lock:
           return [str(key) for key in self.sessions.keys()]

    def get_session(self, session_id: str):
        with self.sessions_lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = TrackerWrapper()
            return self.sessions[session_id]

    def remove_session(self, session_id: str):
        with self.sessions_lock:
            if session_id in self.sessions:
                self.sessions.pop(session_id)
                return True
            else:
                return False
