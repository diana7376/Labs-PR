import socket
import sys
import os
import time
from urllib.parse import unquote

class HTTPServer:
    def __init__(self, host='0.0.0.0', port=8000, document_root='content'):
        self.host = host
        self.port = port
        self.document_root = document_root
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start_server(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(20)
            print(f"Server started on http://{self.host}:{self.port}")
            print(f"Serving files from: {os.path.abspath(self.document_root)}")
            print("Press Ctrl+C to stop the server\n")

            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address[0]}:{client_address[1]}")
                self.handle_client(client_socket)

        except KeyboardInterrupt:
            print("\nServer stopping...")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket):
        try:
            request_data = client_socket.recv(1024).decode('utf-8')
            if not request_data:
                client_socket.close()
                return
            requested_path = self.parse_request(request_data)
            if requested_path is None:
                response = self.create_error_response(400, "Bad Request")
                client_socket.send(response.encode('utf-8'))
            else:
                response = self.serve_file(requested_path)
                if isinstance(response, bytes):
                    client_socket.send(response)
                else:
                    client_socket.send(response.encode('utf-8'))
        except Exception:
            error_response = self.create_error_response(500, "Internal Server Error")
            try:
                client_socket.send(error_response.encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()

    def parse_request(self, request_data):
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
        except Exception:
            return None

    def serve_file(self, requested_path):
        filepath = os.path.join(self.document_root, requested_path)
        abs_document_root = os.path.abspath(self.document_root)
        abs_filepath = os.path.abspath(filepath)
        if not abs_filepath.startswith(abs_document_root):
            return self.create_error_response(403, "Forbidden")
        try:
            if os.path.isfile(filepath):
                return self.serve_single_file(filepath)
            elif os.path.isdir(filepath):
                return self.serve_directory_listing(filepath, requested_path)
            else:
                return self.create_error_response(404, "Not Found")
        except Exception:
            return self.create_error_response(500, "Internal Server Error")

    def serve_single_file(self, filepath):
        try:
            if not self.is_allowed_extension(filepath):
                return self.create_error_response(404, "Not Found")
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
        except Exception:
            return self.create_error_response(500, "Internal Server Error")

    def get_content_type(self, filepath):
        extension = os.path.splitext(filepath)[1].lower()
        content_types = {
            '.html': 'text/html',
            '.htm': 'text/html',
            '.png': 'image/png',
            '.pdf': 'application/pdf'
        }
        return content_types.get(extension, 'application/octet-stream')

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

    def serve_directory_listing(self, dirpath, requested_path):
        items = os.listdir(dirpath)
        items.sort()
        display_path = requested_path.rstrip('/')
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '    <meta charset="UTF-8">',
            f'    <title>Index of /{display_path}</title>',
            '    <style>',
            "body{background:#f8f9fa;font-family:'Segoe UI',Arial,sans-serif;color:#3c4551;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center}",
            ".container{width:90vw;max-width:640px;min-width:300px;min-height:350px;background:#fff;box-shadow:2px 4px 0 0 #2872f7;border:2px solid #2872f7;border-radius:8px;padding:0 0 20px 0;box-sizing:border-box;position:relative}",
            "h1{color:#2872f7;text-align:center;font-weight:600;font-size:1.7em;padding:20px 0 10px 0;border-bottom:1px solid #2872f7;margin-bottom:18px}",
            ".file-list{list-style:none;padding:0}",
            ".file-list li{background:#f8f9fa;margin:8px 0;border-radius:6px;transition:background .2s;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #c2d2f6}",
            ".file-list li:hover{background:#dbe9fe}",
            ".file-list a{display:block;padding:12px 16px;color:#2872f7;text-decoration:none;font-weight:500;font-size:1em}",
            ".file-list a:hover{color:#2872f7;background:#e7f0ff;border-radius:4px}",
            ".directory a{color:#e7b900!important}",
            ".file-info{display:flex;justify-content:space-between;align-items:center}",
            ".file-details{font-size:.85em;color:#8aa8dc;margin-left:20px}",
            '    </style>',
            '</head>',
            '<body>',
            f'    <div class="container"><h1>📁 Index of /{display_path}</h1><ul class="file-list">'
        ]
        # parent directory link
        if requested_path and requested_path != '/':
            parent_path = os.path.dirname(requested_path.rstrip('/'))
            if not parent_path:
                parent_path = '/'
            html_parts.append(f'<li class="directory"><a href="/{parent_path}"> Parent Directory</a></li>')
        # directory listing
        for item in items:
            item_path = os.path.join(dirpath, item)
            stat_info = os.stat(item_path)
            mod_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat_info.st_mtime))
            if os.path.isdir(item_path):
                file_size = "-"
                icon = "📁"
                link = f"/{requested_path}/{item}".replace('//', '/')
                class_name = 'directory'
            else:
                file_size = self.format_size(stat_info.st_size)
                icon = '📄'
                link = f"/{requested_path}/{item}".replace('//', '/')
                class_name = ''
            html_parts.append(
                f'<li class="{class_name}"><a href="{link}">'
                f'<div class="file-info"><span>{icon} {item}</span>'
                f'<span class="file-details">{file_size} | {mod_time}</span></div></a></li>'
            )
        html_parts.append('</ul></div></body></html>')
        html_content = '\n'.join(html_parts)
        content_length = len(html_content.encode('utf-8'))
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{html_content}"
        )
        return response

    def is_allowed_extension(self, filepath):
        extension = os.path.splitext(filepath)[1].lower()
        allowed_extensions = {'.html', '.htm', '.png', '.pdf'}
        return extension in allowed_extensions

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def create_error_response(self, status_code, status_text):
        if status_code == 404:
            # UI-style 404
            html_content = (
                '<!DOCTYPE html>\n'
                '<html>\n'
                '<head>\n'
                '    <meta charset="UTF-8">\n'
                f'    <title>{status_code} - {status_text}</title>\n'
                '<style>\n'
                'body {background: #f8f9fa; font-family: Segoe UI, Arial, sans-serif;}\n'
                '.notfound-container {max-width: 400px; margin: 80px auto; text-align: center; background: #fff; border: 2px solid #2872f7; border-radius: 10px; box-shadow: 2px 4px 0 0 #2872f7; padding: 37px 25px 30px 25px;}\n'
                '.notfound-container h1 {color: #2872f7; font-size: 2em; border-bottom: 1px solid #c2d2f6; padding-bottom: 8px;}\n'
                '.notfound-container p {color: #3c4551; font-size: 1.1em; margin-top: 22px; margin-bottom: 30px;}\n'
                '.notfound-container a {color: #2872f7; text-decoration: none; font-weight: 500; font-size: 1.1em; border: 1px solid #2872f7; border-radius: 6px; padding: 7px 17px; background: #dbe9fe; transition: background 0.2s, color 0.2s;}\n'
                '.notfound-container a:hover {background: #2872f7; color: #fff;}\n'
                '</style>\n'
                '</head>\n'
                '<body>\n'
                '  <div class="notfound-container">\n'
                f'    <h1>{status_code} {status_text}</h1>\n'
                '    <p>The page or file you requested does not exist.</p>\n'
                '    <a href="/">Go Home</a>\n'
                '  </div>\n'
                '</body>\n'
                '</html>\n'
            )
        elif status_code == 429:
            # UI-style ratelimit
            html_content = (
                '<!DOCTYPE html>\n'
                '<html>\n'
                '<head>\n'
                '    <meta charset="UTF-8">\n'
                f'    <title>{status_code} - {status_text}</title>\n'
                '<style>\n'
                'body {background: #f8f9fa; font-family: Segoe UI, Arial, sans-serif; margin: 0; padding: 0;}\n'
                '.container {max-width: 420px; min-height: 300px; margin: 80px auto 0 auto; background: #fff; border: 2px solid #e04b4b; border-radius: 11px; box-shadow: 0 4px 20px rgba(255, 95, 87, 0.09); padding: 38px 32px 32px 32px; text-align: center;}\n'
                '.header {font-size: 1.7em; color: #e04b4b; border-bottom: 1px solid #e3e3e3; padding-bottom: 10px; font-weight: 600; margin-bottom: 12px;}\n'
                '.header-title {font-size: 1.3em; color: #e04b4b; font-weight: bold; letter-spacing: 0.5px;}\n'
                '.big-icon {font-size: 2.2em; color: #e04b4b; margin-bottom: 12px;}\n'
                '.info-message {font-size: 1.2em; color: #3c4551; margin-top: 24px; margin-bottom: 14px;}\n'
                '@media (max-width: 500px) {.container { padding: 18px 8px 18px 8px; } .header-title { font-size: 1.1em; } .info-message { font-size: 1em; }}\n'
                '</style>\n'
                '</head>\n'
                '<body>\n'
                '  <div class="container">\n'
                '    <div class="header">\n'
                '      <span class="header-title">429 Rate Limit Exceeded</span>\n'
                '    </div>\n'
                '    <div style="padding: 48px 32px 0 32px; text-align: center;">\n'
                '      <div class="big-icon">&#9888;</div>\n'
                '      <div class="info-message">\n'
                '        You have sent too many requests.<br>\n'
                '        Please try again after a short pause.\n'
                '      </div>\n'
                '    </div>\n'
                '  </div>\n'
                '</body>\n'
                '</html>\n'
            )
        else:
            # Generic error page with blue accent
            html_content = (
                '<!DOCTYPE html>\n'
                '<html>\n'
                '<head>\n'
                '    <meta charset="UTF-8">\n'
                f'    <title>{status_code} - {status_text}</title>\n'
                '<style>\n'
                'body {background: #f8f9fa; font-family: Segoe UI, Arial, sans-serif;}\n'
                '.container {max-width: 400px; margin: 80px auto; text-align: center; background: #fff; border: 2px solid #2872f7; border-radius: 10px; box-shadow: 2px 4px 0 0 #2872f7; padding: 37px 25px 30px 25px;}\n'
                'h1 {color: #2872f7; font-size: 2em; border-bottom: 1px solid #c2d2f6; padding-bottom: 8px; margin-bottom: 16px;}\n'
                'h2 {color: #3c4551; margin-bottom: 14px;}\n'
                'p {color: #8aa8dc; margin-bottom: 20px; line-height: 1.7;}\n'
                'a {display: inline-block; padding: 10px 20px; background: #2872f7; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 500; transition: background 0.2s;}\n'
                'a:hover {background: #1b4baa;}\n'
                '</style>\n'
                '</head>\n'
                '<body>\n'
                f'  <div class="container">\n'
                f'    <h1>{status_code}</h1>\n'
                f'    <h2>{status_text}</h2>\n'
                '    <p>The server encountered an error processing your request.</p>\n'
                '    <a href="/">Go back to home</a>\n'
                '  </div>\n'
                '</body>\n'
                '</html>\n'
            )
        content_length = len(html_content.encode('utf-8'))
        response = (
            f"HTTP/1.1 {status_code} {status_text}\r\n"
            f"Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{html_content}"
        )
        return response

def main():
    if len(sys.argv) > 1:
        document_root = sys.argv[1]
    else:
        document_root = 'content'
    if not os.path.exists(document_root):
        print(f"Error: Directory '{document_root}' does not exist!")
        print("Please create the directory or specify a different one.")
        return
    server = HTTPServer(document_root=document_root)
    server.start_server()

if __name__ == "__main__":
    main()
