import socket
import os
import mimetypes
import sys

# Get the directory to serve files from, default to 'content'
if len(sys.argv) < 2:
    content_dir = 'content'
else:
    content_dir = sys.argv[1]

HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 8080       # Port number. Change if needed.

# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Allow immediate reuse of address after program exits
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print(f"Serving HTTP on {HOST} port {PORT} (http://localhost:{PORT}/) ...")

def get_content_type(file_path):
    # Guess the MIME type based on file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    else:
        return 'application/octet-stream'  # Default

while True:
    # Accept a client connection
    client_conn, client_addr = server_socket.accept()
    print(f"Got connection from {client_addr}")

    # Read HTTP request data (max 8KB)
    request_data = client_conn.recv(8192).decode('utf-8')
    print(request_data)

    # Parse HTTP request line
    request_lines = request_data.splitlines()
    if not request_lines:
        client_conn.close()
        continue

    request_line = request_lines[0]
    parts = request_line.split()
    if len(parts) < 2 or parts[0] != 'GET':
        # Only accept GET requests
        response = "HTTP/1.1 400 Bad Request\r\n\r\n"
        client_conn.sendall(response.encode())
        client_conn.close()
        continue

    requested_path = parts[1]  # e.g. "/doc1.pdf"

    # Remove leading slash
    file_path = requested_path.lstrip('/')
    file_path = os.path.join(content_dir, file_path)

    if os.path.isfile(file_path):
        # File exists, send it!
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            content_type = get_content_type(file_path)
            response_headers = [
                "HTTP/1.1 200 OK",
                f"content-Type: {content_type}",
                f"content-Length: {len(file_data)}",
                "Connection: close",
                "", ""  # End of headers
            ]
            response_header_bytes = "\r\n".join(response_headers).encode()
            client_conn.sendall(response_header_bytes + file_data)
        except Exception as e:
            # Server error
            response = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
            client_conn.sendall(response.encode())
    else:
        # File not found, send 404 error!
        response_body = b"<h1>404 Not Found</h1>\nThe requested file could not be found."
        response_headers = [
            "HTTP/1.1 404 Not Found",
            "content-Type: text/html",
            f"content-Length: {len(response_body)}",
            "Connection: close",
            "", ""
        ]
        response_header_bytes = "\r\n".join(response_headers).encode()
        client_conn.sendall(response_header_bytes + response_body)

    client_conn.close()
