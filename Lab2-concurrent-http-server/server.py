import socket
import threading
import os
import mimetypes
from urllib.parse import unquote
import time

HOST = "0.0.0.0"
PORT = 8080

file_request_count = {}
counter_lock = threading.Lock()

ip_request_times = {}
rate_lock = threading.Lock()
RATE_LIMIT = 5
WINDOW_SECONDS = 1

def guess_mime(file_path):
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"

def send_response(conn, status_code, content, headers=None):
    reason = {200: "OK", 404: "Not Found", 429: "Too Many Requests"}.get(status_code, "OK")
    header_lines = [
        f"HTTP/1.1 {status_code} {reason}",
        "Connection: close"
    ]
    if headers:
        header_lines.extend(headers)
    header_data = "\r\n".join(header_lines) + "\r\n\r\n"
    if isinstance(content, str):
        content = content.encode()
    conn.sendall(header_data.encode() + content)

def get_icon_class(item_path):
    if os.path.isdir(item_path):
        return "icon-folder"
    ext = os.path.splitext(item_path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif"]:
        return "icon-img"
    if ext == ".pdf":
        return "icon-pdf"
    if ext == ".css":
        return "icon-css"
    if ext == ".js":
        return "icon-js"
    return "icon-file"

def get_parent_url(rel_path):
    clean = rel_path.rstrip("/")
    if not clean or clean == "/":
        return None
    parts = clean.split("/")
    parent = "/" + "/".join(parts[:-1])
    return parent if parent != "/" else "/"

def generate_dir_listing(directory, rel_path, template_path=None):
    if template_path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base, "files", "pages", "listing_template.html")
    items = os.listdir(directory)
    list_items = ""
    for item in items:
        item_path = os.path.join(directory, item)
        icon_class = get_icon_class(item_path)
        link = os.path.join(rel_path, item).replace("\\", "/")
        icon_html = f'<span class="icon {icon_class}"></span>'
        if os.path.isdir(item_path):
            list_items += f'<li>{icon_html}<a class="folder-link" href="{link}/">{item}/</a></li>\n'
        else:
            with counter_lock:
                count = file_request_count.get(item_path, 0)
            list_items += f'<li>{icon_html}<a class="file-link" href="{link}">{item}</a> <span class="file-count">[{count}]</span></li>\n'
    parent_url = get_parent_url(rel_path)
    arrow_html = (
        f'<a class="back-arrow" href="{parent_url}" title="Go up"></a> '
        if parent_url else ""
    )
    header_html = (
        f'<div class="header-row">'
        f'{arrow_html}'
        f'<span class="header-title">{rel_path if rel_path not in ["", "/"] else "/"}</span>'
        f'</div>'
    )
    try:
        with open(template_path, "r", encoding="utf-8") as tpl:
            html = tpl.read()
        html = html.replace("{{directory}}", header_html)
        html = html.replace("{{items}}", list_items)
    except Exception as e:
        html = f"<html><body><h2>Directory: {rel_path}</h2><ul>{list_items}</ul></body></html>"
        print(f"Template error: {e}")
    return html

def load_404_page(template_path=None):
    if template_path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base, "files", "pages", "404.html")
    try:
        with open(template_path, "r", encoding="utf-8") as tpl:
            return tpl.read()
    except Exception as e:
        print(f"404 template error: {e}")
        return "<h1>404 Not Found</h1>"

def load_ratelimit_page(template_path=None):
    if template_path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base, "files", "pages", "ratelimit.html")
    try:
        with open(template_path, "r", encoding="utf-8") as tpl:
            return tpl.read()
    except Exception as e:
        print(f"Rate limit template error: {e}")
        return "<h1>Rate limit exceeded</h1>"

def handle_client(conn, addr, base_dir, listing_tpl_path=None, tpl_404_path=None):
    try:
        request = conn.recv(4096).decode()
        if not request:
            return
        client_ip = addr[0]
        now = time.time()
        with rate_lock:
            times = ip_request_times.get(client_ip, [])
            times = [t for t in times if now - t < WINDOW_SECONDS]
            if len(times) >= RATE_LIMIT:
                content_rl = load_ratelimit_page()
                send_response(conn, 429, content_rl, headers=["Content-Type: text/html"])
                return
            times.append(now)
            ip_request_times[client_ip] = times

        lines = request.splitlines()
        if not lines:
            return
        method, path, *_ = lines[0].split()
        path = unquote(path)
        req_path = path.lstrip("/")
        fs_path = os.path.join(base_dir, req_path)
        if path == "/" or path == "":
            content = generate_dir_listing(base_dir, "/", template_path=listing_tpl_path)
            send_response(conn, 200, content, headers=["Content-Type: text/html"])
            return
        if method != "GET":
            content_404 = load_404_page(tpl_404_path)
            send_response(conn, 404, content_404, headers=["Content-Type: text/html"])
            return
        if os.path.isdir(fs_path):
            if not path.endswith("/"):
                send_response(conn, 200, "", headers=[f"Location: {path}/"])
                return
            content = generate_dir_listing(fs_path, path, template_path=listing_tpl_path)
            send_response(conn, 200, content, headers=["Content-Type: text/html"])
            return
        if os.path.isfile(fs_path):
            with counter_lock:
                file_request_count[fs_path] = file_request_count.get(fs_path, 0) + 1
            with open(fs_path, "rb") as f:
                content = f.read()
            mime = guess_mime(fs_path)
            send_response(conn, 200, content, headers=[f"Content-Type: {mime}"])
            return
        content_404 = load_404_page(tpl_404_path)
        send_response(conn, 404, content_404, headers=["Content-Type: text/html"])
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

def start_server(base_dir, listing_tpl_path=None, tpl_404_path=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Serving {base_dir} at http://{HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(
                conn, addr, base_dir, listing_tpl_path, tpl_404_path
            ))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python server.py <serve_directory> [<listing_tpl_path> [<404_tpl_path>]]")
        sys.exit(1)
    base_dir = sys.argv[1]
    listing_tpl_path = sys.argv[2] if len(sys.argv) > 2 else None
    tpl_404_path = sys.argv[3] if len(sys.argv) > 3 else None
    start_server(base_dir, listing_tpl_path, tpl_404_path)
