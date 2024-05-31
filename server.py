import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict
from threading import Lock
import sys

response_sequence = [
    ("200", "2cba8153f2ff", 1000),
    ("200", "123", 100),
    # ("404", "", 200),
]


class MyHandler(BaseHTTPRequestHandler):
    response_index = 0
    request_counts = defaultdict(int)
    blocked_addresses = set()
    lock = Lock()

    def do_GET(self):
        client_address = self.client_address[0]

        with MyHandler.lock:
            # Check if the client is blocked and respond accordingly
            if client_address in MyHandler.blocked_addresses:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({}).encode())
                print(f"Blocked request from {client_address}")
                return

            # Track requests and block the client if it exceeds the request limit - 30
            MyHandler.request_counts[client_address] += 1
            if MyHandler.request_counts[client_address] > 30:
                MyHandler.blocked_addresses.add(client_address)
                MyHandler.request_counts[client_address] -= 1
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({}).encode())
                print(f"Blocked request from {client_address}")
                return

        code, payload, delay = response_sequence[MyHandler.response_index]
        MyHandler.response_index = (MyHandler.response_index + 1) % len(response_sequence)

        time.sleep(delay / 1000.0)

        # Send the response to the client
        self.send_response(int(code))
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if code == "200":
            response = {"information": payload}
        else:
            response = {}

        self.wfile.write(json.dumps(response).encode())

        # Decrement the request count for the client
        with MyHandler.lock:
            MyHandler.request_counts[client_address] -= 1

        print(f"Handled request from {client_address} with code {code}, payload {payload}, after {delay}ms delay")


# Function to run the HTTP server.
def run(server_class=HTTPServer, handler_class=MyHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("default example responses")
    elif len(sys.argv) == 2:
        print("responses from path")
        path_to_serv_response = sys.argv[0]
    else:
        print("Too many arguments. Usage python server.py <responses path>.")
        sys.exit(1)
    run()
