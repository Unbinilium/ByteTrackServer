from typing import Tuple

import time
import json
import logging
import threading

import socketserver
from http import HTTPStatus, server

from bytetrack.session_manager import SessionManager
from bytetrack.sscma_utilitiy import parse_bytes_to_json

shared_session_manager = SessionManager()

class Handler(server.SimpleHTTPRequestHandler):
    def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server)

    def verify_path(self):
        if not self.path == '/':
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return False
        return True

    def verify_content_type(self):
        if not self.headers['Content-Type'] == 'application/json':
            self.send_response(HTTPStatus.NOT_ACCEPTABLE)
            self.end_headers()
            return False
        return True

    def verify_session_id(self):
        if not 'Session-Id' in self.headers:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            return False
        if len(self.headers['Session-Id']) < 1:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            return False
        return True

    def verify_content_length(self):
        if not 'Content-Length' in self.headers:
            self.send_response(HTTPStatus.LENGTH_REQUIRED)
            self.end_headers()
            return False
        return True

    @property
    def api_response(self):
        logging.info(self.headers)
        response = dict()
        response['sessions'] = shared_session_manager.get_sessions()
        response['active_threads']= threading.active_count()
        response['timestamp'] = time.time()
        return json.dumps(response).encode()

    def do_GET(self):
        if not (self.verify_path()):
            return
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(self.api_response))

    def do_POST(self):
        if not (self.verify_path() and self.verify_content_type() and self.verify_session_id() and self.verify_content_length()):
            return
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            post_json = parse_bytes_to_json(post_data)
            session = shared_session_manager.get_session(self.headers['Session-Id'])
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        except ValueError:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            return
        response = session.track_with_detections(post_json)
        response['timestamp'] = time.time()
        self.wfile.write(bytes(json.dumps(response).encode()))

    def do_DELETE(self):
        if not (self.verify_path() and self.verify_session_id()):
            return
        if not shared_session_manager.remove_session(self.headers['Session-Id']):
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.end_headers()
            return
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write(bytes(self.api_response))
