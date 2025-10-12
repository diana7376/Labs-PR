import socket
import sys
import os

def http_client(host, port, filename):
    # Create TCP client socket and connect to host:port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"Connected to {host}:{port}")

    # Craft HTTP GET request
    request_line = f"GET /{filename} HTTP/1.1\r\n"
    headers = f"Host: {host}\r\nConnection: close\r\n\r\n"
    http_request = request_line + headers

    # Send HTTP request
    sock.sendall(http_request.encode())

    # Receive response data (max 4MB)
    response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    sock.close()

    # Separate headers and body
    split_index = response.find(b"\r\n\r\n")
    if split_index == -1:
        print("Invalid HTTP response!")
        return

    headers_raw = response[:split_index].decode(errors="ignore")
    body = response[split_index+4:]
    print("---- Response Headers ----")
    print(headers_raw)
    print("--------")

    # Decide what to do based on file extension
    if filename.endswith(".html"):
        print("---- HTML Output ----")
        print(body.decode(errors="ignore"))
    elif filename.endswith(".pdf") or filename.endswith(".jpg") or filename.endswith(".png"):
        # Save to disk
        local_name = f"downloaded_{os.path.basename(filename)}"
        with open(local_name, "wb") as f:
            f.write(body)
        print(f"Downloaded file saved as '{local_name}'")
    else:
        print("---- Raw Output ----")
        print(body.decode(errors="ignore"))

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python client.py <server_host> <server_port> <filename>")
        print("Example: python client.py localhost 8080 index.html")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]
    http_client(host, port, filename)
