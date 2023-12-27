from threading import Lock

import secrets

from bytetrack.tracker_wrapper import TrackerWrapper
from bytetrack.utilitiy import SessionConfig


class SessionManager:
    def __init__(self, max_sessions: int = 32):
        self.sessions_lock = Lock()
        self.sessions = {}
        self.max_sessions = max_sessions

    def create_session(self, session_config: SessionConfig):
        with self.sessions_lock:
            if len(self.sessions) >= self.max_sessions:
                raise ResourceWarning(f"Max sessions exceeded the limit of {self.max_sessions}")
            new_id = secrets.token_hex(4)
            while new_id in self.sessions:
                new_id = secrets.token_hex(4)
            new_session = TrackerWrapper(session_config)
            self.sessions[new_id] = new_session
        return new_id

    def get_session(self, session_id: str):
        with self.sessions_lock:
            if session_id in self.sessions:
                return self.sessions[session_id]
            raise ValueError(f"Session {session_id} not exist")

    def get_all_sessions_id(self):
        with self.sessions_lock:
            return [str(key) for key in self.sessions]

    def remove_session(self, session_id: str):
        with self.sessions_lock:
            if session_id in self.sessions:
                self.sessions.pop(session_id)
                return True
            return False

    def remove_all_sessions(self):
        with self.sessions_lock:
            self.sessions = {}
