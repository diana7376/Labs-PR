import socket
import sys
import os
import datetime
import time
import threading
from urllib.parse import unquote, quote
from collections import defaultdict
from typing import Dict, List

def get_file_icon(filename):
    ext = filename.split('.')[-1].lower()
    icons = {
        'pdf': '📄',
        'docs': '📄',
        'html': '🌐',
        'png': '🖼️',
        'jpg': '🖼️'
    }
    return icons.get(ext, '📄')
class ConcurrentHTTPServer:
    def __init__(self, host='0.0.0.0', port=8000, document_root='content', use_thread_pool=True, max_workers=10):
        self.host = host
        self.port = port
        self.document_root = document_root
        self.use_thread_pool = use_thread_pool
        self.max_workers = max_workers

        # Request counter - will demonstrate race condition
        self.request_counter = {}
        self.counter_lock = threading.Lock()

        # Rate limiting - per IP tracking
        self.rate_limit_data = defaultdict(lambda: {'requests': [], 'blocked': 0})
        self.rate_limit_lock = threading.Lock()
        self.rate_limit = 5  # requests per second

        # Thread pool
        if use_thread_pool:
            from concurrent.futures import ThreadPoolExecutor
            self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.total_requests = 0
        self.stats_lock = threading.Lock()

    def start_server(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            print(f" Concurrent Server started on http://{self.host}:{self.port}")
            print(f" Serving files from: {os.path.abspath(self.document_root)}")
            print(f" Mode: {'Thread Pool' if self.use_thread_pool else 'Thread per Request'}")
            if self.use_thread_pool:
                print(f" Thread Pool Size: {self.max_workers}")
            print(f" Rate Limit: {self.rate_limit} requests/second per IP")
            print("Press Ctrl+C to stop the server\n")

            while True:
                client_socket, client_address = self.server_socket.accept()

                with self.stats_lock:
                    self.total_requests += 1

                print(f" New connection from {client_address[0]}:{client_address[1]} (Total: {self.total_requests})")

                if self.use_thread_pool:
                    self.thread_pool.submit(self.handle_client, client_socket, client_address)
                else:
                    # Create new thread per request
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

        except KeyboardInterrupt:
            print("\n Server stopping...")
            self.print_statistics()
        except Exception as e:
            print(f" Server error: {e}")
        finally:
            if self.use_thread_pool:
                self.thread_pool.shutdown(wait=True)
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        try:
            client_ip = client_address[0]

            # Check rate limit
            if not self.check_rate_limit(client_ip):
                print(f" Rate limit exceeded for {client_ip}")
                response = self.create_rate_limit_response()
                client_socket.send(response.encode('utf-8'))
                client_socket.close()
                return

            request_data = client_socket.recv(4096).decode('utf-8')
            if not request_data:
                #client_socket.close()
                return

            print(f" [{threading.current_thread().name}] Processing request from {client_ip}")

            time.sleep(1)

            requested_path = self.parse_request(request_data)
            if requested_path == '/stats':
                self.handle_stats_request(client_socket)
                return
            if requested_path is None:
                response = self.create_error_response(400, "Bad Request")
                client_socket.send(response.encode('utf-8'))
            else:
                response = self.serve_file(requested_path)
                if isinstance(response, bytes):
                    client_socket.send(response)
                else:
                    client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f" Error handling client: {e}")
            error_response = self.create_error_response(500, "Internal Server Error")
            try:
                client_socket.send(error_response.encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()



    def check_rate_limit(self, client_ip):
        #Check if client IP has exceeded rate limit (thread-safe)
        with self.rate_limit_lock:
            current_time = time.time()
            client_data = self.rate_limit_data[client_ip]

            # Remove requests older than 1 second
            client_data['requests'] = [
                req_time for req_time in client_data['requests']
                if current_time - req_time < 1.0
            ]

            # Check if under rate limit
            if len(client_data['requests']) >= self.rate_limit:
                client_data['blocked'] += 1
                return False

            # Add current request
            client_data['requests'].append(current_time)
            return True

    def increment_file_counter_naive(self, filepath):
        #NAIVE implementation - NO LOCK - will cause race condition
        current = self.request_counter.get(filepath, 0)
        time.sleep(0.01)
        self.request_counter[filepath] = current + 1

        print(f"   [NAIVE] Thread {threading.current_thread().name}: "
              f"Read {current}, Writing {current + 1} for {os.path.basename(filepath)}")

    def increment_file_counter_safe(self, filepath):
        #THREAD-SAFE implementation using lock
        with self.counter_lock:
            current = self.request_counter.get(filepath, 0)
            time.sleep(0.01)
            new_value = current + 1
            self.request_counter[filepath] = new_value

            print(f"   [SAFE] Thread {threading.current_thread().name}: "
                  f"Read {current}, Writing {new_value} for {os.path.basename(filepath)}")

    def parse_request(self, request_data):
        #Parse an HTTP request and extract the GET request
        try:
            lines = request_data.split('\n')
            if not lines:
                return None

            request_line = lines[0].strip()
            parts = request_line.split(' ')

            if len(parts) < 2:
                return None

            method = parts[0]
            path = parts[1]

            if method != 'GET':
                return None
            path = unquote(path)
            if path.startswith('/'):
                path = path[1:]
            if not path:
                path = 'index.html'
            return path

        except Exception as e:
            print(f" Error parsing request: {e}")
            return None

    def serve_file(self, requested_path):
        #Serve requested file or directory listing
        if requested_path == 'stats' or requested_path == 'stats.json':
            return self.serve_stats_json()

        if requested_path == 'files' or requested_path == 'files.json':
            return self.serve_files_list_json()

        filepath = os.path.join(self.document_root, requested_path)
        abs_document_root = os.path.abspath(self.document_root)
        abs_filepath = os.path.abspath(filepath)

        if not abs_filepath.startswith(abs_document_root):
            return self.create_error_response(403, "Forbidden")

        try:
            if os.path.isfile(filepath):
                # naive implementation to get race condition
                # self.increment_file_counter_naive(filepath)

                #thread safe implementation
                self.increment_file_counter_safe(filepath)


                return self.serve_single_file(filepath)
            elif os.path.isdir(filepath):
                return self.serve_directory_listing(filepath, requested_path)
            else:
                return self.create_error_response(404, "Not Found")

        except Exception as e:
            print(f" Error serving file '{requested_path}': {e}")
            return self.create_error_response(500, "Internal Server Error")

    def serve_stats_json(self):
        try:
            stats = {}
            with self.counter_lock:
                for filepath, count in self.request_counter.items():
                    # Extract just the filename from the full path
                    filename = os.path.basename(filepath)
                    stats[filename] = count

            import json
            json_data = json.dumps(stats)

            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(json_data)}\r\n"
                f"Access-Control-Allow-Origin: *\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{json_data}"
            )

            return response.encode('utf-8')

        except Exception as e:
            print(f" Error creating stats JSON: {e}")
            return self.create_error_response(500, "Internal Server Error")

    def serve_files_list_json(self):
        try:
            import json

            files_data = {
                'images': [],
                'documents': [],
                'directories': []
            }

            items = os.listdir(self.document_root)
            items.sort()

            for item in items:
                if item.startswith('.') or item == 'index.html':
                    continue

                item_path = os.path.join(self.document_root, item)

                if os.path.isdir(item_path):
                    files_data['directories'].append(item)
                elif os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.gif']:
                        files_data['images'].append(item)
                    elif ext in ['.pdf', '.doc', '.docx', '.docs', '.txt', '.html']:
                        files_data['documents'].append(item)

            json_data = json.dumps(files_data)

            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(json_data)}\r\n"
                f"Access-Control-Allow-Origin: *\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{json_data}"
            )

            return response.encode('utf-8')

        except Exception as e:
            print(f" Error creating files list JSON: {e}")
            return self.create_error_response(500, "Internal Server Error")

    def serve_single_file(self, filepath):
        try:
            content_type = self.get_content_type(filepath)
            if content_type == 'text/html':
                content_type = 'text/html; charset=utf-8'

            with open(filepath, 'rb') as f:
                content = f.read()

            content_length = len(content)

            response_headers = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {content_length}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            )

            return response_headers.encode('utf-8') + content

        except Exception as e:
            print(f" Error reading file '{filepath}': {e}")
            return self.create_error_response(500, "Internal Server Error")

    def get_content_type(self, filepath):
        extension = os.path.splitext(filepath)[1].lower()
        content_types = {
            '.html': 'text/html',
            '.htm': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.pdf': 'application/pdf',
            '.css': 'text/css',
            '.js': 'application/javascript'
        }
        return content_types.get(extension, 'application/octet-stream')

    def serve_directory_listing(self, dirpath, requested_path):
        try:
            items = os.listdir(dirpath)
            items.sort()

            display_path = requested_path.rstrip('/')

            html_parts = [
                '<!DOCTYPE html>',
                '<html>',
                '<head>',
                '<meta charset="UTF-8">',
                f'<title>Directory listing for {display_path or "/"}</title>',
                '<style>',
                "body{background:#f8f9fa;font-family:'Segoe UI',Arial,sans-serif;color:#3c4551;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center}",
                ".container{width:90vw;max-width:640px;min-width:300px;min-height:350px;background:#fff;box-shadow:2px 4px 0 0 #2872f7;border:2px solid #2872f7;border-radius:8px;padding:0 0 20px 0;box-sizing:border-box;position:relative}",
                "h1{color:#2872f7;text-align:center;font-weight:600;font-size:1.7em;padding:20px 0 10px 0;border-bottom:1px solid #2872f7;margin-bottom:18px}",
                ".file-list{list-style:none;padding:0}",
                ".file-list li{background:#f8f9fa;margin-left: 10px; margin-right: 10px; margin-top:10px; border-radius:6px;transition:background .2s;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #c2d2f6}",
                ".file-list li:hover{background:#dbe9fe}",
                ".file-list a{display:block;padding:12px 16px;color:#2872f7;text-decoration:none;font-weight:500;font-size:1em}",
                ".file-list a:hover{color:#2872f7;background:#e7f0ff;border-radius:4px}",
                ".directory a{color:#e7b900!important}",
                ".file-info{display:flex;justify-content:space-between;align-items:center}",
                ".file-details{font-size:.85em;color:#8aa8dc;margin-left:20px}",
                '</style>',
                '</head>',
                '<body>',
                f'<div class="container"><h1 style = "margin-left: 10px; margin-right: 10px;" >Directory listing for /{display_path or "/"}</h1><ul class="file-list">'
            ]

            for item in items:
                if item.startswith('.'):
                    continue

                item_path = os.path.join(dirpath, item)
                item_url = quote(item)

                if requested_path and not requested_path.endswith('/'):
                    full_url = f"/{requested_path}/{item_url}"
                else:
                    full_url = f"/{requested_path}{item_url}"

                if os.path.isdir(item_path):
                    full_url += '/'
                    icon = "📁"
                    display_name = ' ' + item
                    hits = '--'
                    li_class = ' class="directory"'
                else:
                    icon = get_file_icon(item)
                    display_name = ' ' + item
                    with self.counter_lock:
                        hits = f"{self.request_counter.get(item_path, 0)} hits"
                    li_class = ''

                html_parts.append(f'            <li{li_class}>')
                html_parts.append(f'                <a href="{full_url}">{icon} {display_name}</a>')

                html_parts.append(f'                <span style = "margin-left: 10px; margin-right: 10px;  class="hit-counter">{hits}</span>')
                html_parts.append(f'            </li>')

            html_parts.extend([
                '        </ul>',
                '    </div>',
                '</body>',
                '</html>'
            ])

            html_content = '\n'.join(html_parts)
            content_bytes = html_content.encode('utf-8')

            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(content_bytes)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            )

            return response.encode('utf-8') + content_bytes

        except Exception as e:
            print(f" Error creating directory listing: {e}")
            return self.create_error_response(500, "Internal Server Error")

    def create_error_response(self, status_code, status_message):
        html_content = (
            '<!DOCTYPE html>\n'
            '<html>\n'
            '<head>\n'
            '<meta charset="UTF-8">\n'
            f'<title>{status_code} {status_message}</title>\n'
            '<style>\n'
            "body {background: #f8f9fa; font-family: Segoe UI, Arial, sans-serif;}\n"
            ".notfound-container {max-width: 400px; margin: 80px auto; text-align: center; background: #fff; border: 2px solid #2872f7; border-radius: 10px; box-shadow: 2px 4px 0 0 #2872f7; padding: 37px 25px 30px 25px;}\n"
            ".notfound-container h1 {color: #2872f7; font-size: 2em; border-bottom: 1px solid #c2d2f6; padding-bottom: 8px;}\n"
            ".notfound-container p {color: #3c4551; font-size: 1.1em; margin-top: 22px; margin-bottom: 30px;}\n"
            ".notfound-container a {color: #2872f7; text-decoration: none; font-weight: 500; font-size: 1.1em; border: 1px solid #2872f7; border-radius: 6px; padding: 7px 17px; background: #dbe9fe; transition: background 0.2s, color 0.2s;}\n"
            ".notfound-container a:hover {background: #2872f7; color: #fff;}\n"
            '</style>\n'
            '</head>\n'
            '<body>\n'
            '<div class="notfound-container">\n'
            f'<h1>{status_code} - {status_message}</h1>\n'
            '<p>The server encountered an error processing your request.</p>\n'
            '<a href="/">Go back to home</a>\n'
            '</div>\n'
            '</body>\n'
            '</html>\n'
        )

        response = (
            f"HTTP/1.1 {status_code} {status_message}\r\n"
            f"Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(html_content)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{html_content}"
        )

        return response

    def create_rate_limit_response(self):
        html_content = (
            '<!DOCTYPE html>\n'
            '<html>\n'
            '<head>\n'
            '<meta charset="UTF-8">\n'
            '<title>429 Too Many Requests</title>\n'
            '<style>\n'
            "body {background: #f8f9fa; font-family: Segoe UI, Arial, sans-serif; margin: 0; padding: 0;}\n"
            ".container {max-width: 420px; min-height: 300px; margin: 80px auto 0 auto; background: #fff; border: 2px solid #e04b4b; border-radius: 11px; box-shadow: 0 4px 20px rgba(255, 95, 87, 0.09); padding: 38px 32px 32px 32px; text-align: center;}\n"
            ".header {font-size: 1.7em; color: #e04b4b; border-bottom: 1px solid #e3e3e3; padding-bottom: 10px; font-weight: 600; margin-bottom: 12px;}\n"
            ".header-title {font-size: 1.3em; color: #e04b4b; font-weight: bold; letter-spacing: 0.5px;}\n"
            ".big-icon {font-size: 2.2em; color: #e04b4b; margin-bottom: 12px;}\n"
            ".info-message {font-size: 1.2em; color: #3c4551; margin-top: 24px; margin-bottom: 14px;}\n"
            "@media (max-width: 500px) {.container { padding: 18px 8px 18px 8px; } .header-title { font-size: 1.1em; } .info-message { font-size: 1em; }}\n"
            '</style>\n'
            '</head>\n'
            '<body>\n'
            '<div class="container">\n'
            '<div class="header"><span class="header-title">429 Rate Limit Exceeded</span></div>\n'
            '<div style="padding: 48px 32px 0 32px; text-align: center;">\n'
            '<div class="big-icon">&#9888;</div>\n'
            '<div class="info-message">\n'
            'You have sent too many requests.<br>\n'
            'Please try again after a short pause.\n'
            '</div>\n'
            '</div>\n'
            '</div>\n'
            '</body>\n'
            '</html>\n'
        )

        response = (
            f"HTTP/1.1 429 Too Many Requests\r\n"
            f"Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(html_content)}\r\n"
            f"Retry-After: 1\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{html_content}"
        )

        return response

    def print_statistics(self):
        print("\n" + "=" * 50)
        print(" Server Statistics")
        print("=" * 50)
        print(f"Total requests handled: {self.total_requests}")
        print(f"\n File access counts:")
        with self.counter_lock:
            for filepath, count in sorted(self.request_counter.items(), key=lambda x: x[1], reverse=True):
                print(f"  {os.path.basename(filepath)}: {count}")

        print(f"\n Rate limit blocks per IP:")
        with self.rate_limit_lock:
            for ip, data in self.rate_limit_data.items():
                if data['blocked'] > 0:
                    print(f"  {ip}: {data['blocked']} blocked requests")


def main():
    if len(sys.argv) < 2:
        print("Usage: python concurrent_server.py [thread-pool|thread-per-request] [port] [max_workers]")
        print("Example: python concurrent_server.py thread-pool 8000 10")
        print("Example: python concurrent_server.py thread-per-request 8000")
        return

    mode = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    use_thread_pool = (mode == 'thread-pool')

    server = ConcurrentHTTPServer(
        host='0.0.0.0',
        port=port,
        document_root='content',
        use_thread_pool=use_thread_pool,
        max_workers=max_workers
    )

    server.start_server()


if __name__ == "__main__":
    main()
