from socketserver import ThreadingMixIn
from http.server import HTTPServer
from concurrent.futures import ThreadPoolExecutor

from bytetrack.service_handler import Handler


class PooledHTTPServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, max_workers=4):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.pool = ThreadPoolExecutor(max_workers=max_workers)

    def process_request(self, request, client_address):
        self.pool.submit(self.process_request_thread, request, client_address)

class ByteTrackServer():
    def __init__(self, host: str, port: int, ssl: bool, ssl_certfile: str, ssl_keyfile: str, max_workers: int):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile
        self.max_workers = max_workers

    def start(self):
        server = PooledHTTPServer((self.host, self.port), Handler, max_workers=self.max_workers)
        if self.ssl:
            import ssl
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=self.ssl_certfile, keyfile=self.ssl_keyfile)
            server.socket = context.wrap_socket(server.socket, server_side=True)
        server.serve_forever()
