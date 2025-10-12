import socket
import os
import mimetypes
import sys
from urllib.parse import unquote

def get_content_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def render_directory_listing(folder, rel_path, abs_path):
    with open('dir_listing.html', 'r', encoding='utf-8') as f:
        template = f.read()
    items = os.listdir(abs_path)
    links = []
    for name in items:
        item_path = os.path.join(rel_path, name).replace("\\", "/")
        if os.path.isdir(os.path.join(abs_path, name)):
            display = f"{name}/"
        else:
            display = name
        links.append(f'<li><a class="file-link" href="/{item_path}">{display}</a></li>')
    # Compute parent folder URL
    upurl = "/" + "/".join(rel_path.rstrip("/").split("/")[:-1])
    if upurl == "/":
        upurl = "/"  # go to homepage if at root
    backurl = upurl
    html = template.replace('{{FOLDER}}', folder)
    html = html.replace('{{LINKS}}', ''.join(links))
    html = html.replace('{{BACKURL}}', backurl)
    return html.encode()


if len(sys.argv) < 2:
    content_dir = 'content'
else:
    content_dir = sys.argv[1]

HOST = '0.0.0.0'
PORT = 8080

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print(f"Serving HTTP on {HOST} port {PORT} (http://localhost:{PORT}/) ...")

while True:
    client_conn, client_addr = server_socket.accept()
    request_data = client_conn.recv(8192).decode('utf-8')

    request_lines = request_data.splitlines()
    if not request_lines:
        client_conn.close()
        continue

    request_line = request_lines[0]
    parts = request_line.split()
    if len(parts) < 2 or parts[0] != 'GET':
        response = "HTTP/1.1 400 Bad Request\r\n\r\n"
        client_conn.sendall(response.encode())
        client_conn.close()
        continue

    requested_path = unquote(parts[1])
    rel_path = requested_path.lstrip('/')
    abs_path = os.path.join(content_dir, rel_path)

    print("REQUESTED:", requested_path)
    print("REL_PATH:", rel_path)
    print("ABS_PATH:", abs_path)
    print("IS DIR?", os.path.isdir(abs_path))
    print("IS FILE?", os.path.isfile(abs_path))

    if os.path.isfile(abs_path):
        try:
            with open(abs_path, 'rb') as f:
                file_data = f.read()
            content_type = get_content_type(abs_path)
            response_headers = [
                "HTTP/1.1 200 OK",
                f"Content-Type: {content_type}",
                f"Content-Length: {len(file_data)}",
                "Connection: close",
                "", ""
            ]
            response = "\r\n".join(response_headers).encode() + file_data
            client_conn.sendall(response)
        except Exception:
            response = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
            client_conn.sendall(response.encode())
    elif os.path.isdir(abs_path):
        try:
            folder_name = rel_path if rel_path else content_dir
            response_body = render_directory_listing(folder_name, rel_path, abs_path)
            response_headers = [
                "HTTP/1.1 200 OK",
                "Content-Type: text/html",
                f"Content-Length: {len(response_body)}",
                "Connection: close",
                "", ""
            ]
            response = "\r\n".join(response_headers).encode() + response_body
            client_conn.sendall(response)
        except Exception:
            response = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
            client_conn.sendall(response.encode())
    else:
        response_body = b"<h1>404 Not Found</h1><p>The requested file or folder does not exist.</p>"
        response_headers = [
            "HTTP/1.1 404 Not Found",
            "Content-Type: text/html",
            f"Content-Length: {len(response_body)}",
            "Connection: close",
            "", ""
        ]
        response = "\r\n".join(response_headers).encode() + response_body
        client_conn.sendall(response)

    client_conn.close()
