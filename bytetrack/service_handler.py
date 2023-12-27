from typing import Tuple, List

import time
import json
import threading

import socketserver
import http
from http import HTTPStatus

from bytetrack.session_manager import SessionManager
from bytetrack.utilitiy import parse_bytes_to_json, SessionConfig


shared_session_manager = SessionManager()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(
        self,
        request: bytes,
        client_address: Tuple[str, int],
        server: socketserver.BaseServer,
    ):
        super().__init__(request, client_address, server)

    def verify_content_type(self):
        if not self.headers["Content-Type"] == "application/json":
            self.send_response(HTTPStatus.NOT_ACCEPTABLE)
            self.end_headers()
            return False
        return True

    def verify_content_length(self):
        if not "Content-Length" in self.headers:
            self.send_response(HTTPStatus.LENGTH_REQUIRED)
            self.end_headers()
            return False
        return True

    @property
    def api_response(self):
        response = {}
        response["sessions"] = shared_session_manager.get_all_sessions_id()
        response["active_threads"] = threading.active_count()
        response["status"] = "OK"
        response["message"] = ""
        response["timestamp"] = time.time()
        return json.dumps(response).encode()

    def do_GET(self):
        if self.path != "/":
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(bytes(self.api_response))
        self.wfile.flush()

    def do_POST(self):
        if not (self.verify_content_type() and self.verify_content_length()):
            return

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        try:
            post_json = parse_bytes_to_json(post_data)
            if (self.path == "/"):
                session_config = SessionConfig(**post_json)
                session_id = shared_session_manager.create_session(session_config)
                self.send_response(HTTPStatus.OK)
                self.send_header("Session-Id", session.session_id)
                self.end_headers()
                return
            session = shared_session_manager.get_session(self.headers["Session-Id"])
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
        except Exception:  # pylint: disable=broad-except
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            return
        response = session.track_with_detections(post_json)
        response["timestamp"] = time.time()
        self.wfile.write(bytes(json.dumps(response).encode()))
        self.wfile.flush()

    def do_DELETE(self):
        if not (self.verify_path() and self.verify_session_id()):
            return
        if not shared_session_manager.remove_session(self.headers["Session-Id"]):
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.end_headers()
            return
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write(bytes(self.api_response))
        self.wfile.flush()
