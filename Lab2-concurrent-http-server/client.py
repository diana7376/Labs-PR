import sys
import os
import requests
import threading
import time

def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def save_file(content, directory, filename):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, filename), "wb") as f:
        f.write(content)
    print(color(f"[Saved] {filename} to '{directory}'", "92"))  # Green

def handle_response(resp, save_dir, urlpath):
    content_type = resp.headers.get("Content-Type", "")
    filename = urlpath.strip("/").split("/")[-1] or "listing_template.html"
    if resp.status_code == 429:
        print(color("[RATE LIMIT EXCEEDED] Too many requests. Try again later.", "93"))
    elif "text/html" in content_type:
        print(color(f"[HTML Content]", "94"))
        print(resp.text)
    elif "png" in content_type or "pdf" in content_type:
        save_file(resp.content, save_dir, filename)
    else:
        print(color(f"[Unknown Type: {content_type}]", "93"))
        print(resp.text)


def client_thread(host, port, urlpath, directory, repeat=1, delay=0):
    url = f"http://{host}:{port}/{urlpath.lstrip('/')}"
    for _ in range(repeat):
        try:
            resp = requests.get(url)
            prefix = color(f"[{threading.current_thread().name}]", "96")
            print(f"{prefix} Status: {resp.status_code} | URL: {url}")
            handle_response(resp, directory, urlpath)
            time.sleep(delay)
        except Exception as e:
            prefix = color(f"[{threading.current_thread().name}]", "91")
            print(f"{prefix} Error: {e}")

def run_concurrent_clients(host, port, urlpath, directory, num_threads=10, repeat=1, delay=0):
    threads = []
    start = time.time()
    print(color(f"Starting {num_threads} client threads...", "95"))
    for i in range(num_threads):
        t = threading.Thread(target=client_thread, args=(host, port, urlpath, directory, repeat, delay), name=f"Client-{i+1}")
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    elapsed = time.time() - start
    print(color(f"All clients finished in {elapsed:.2f} seconds.", "92"))

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(color("Usage: python client.py <serverhost> <serverport> <urlpath> <directory> [num_threads] [repeat] [delay]", "93"))
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    urlpath = sys.argv[3]
    directory = sys.argv[4]
    num_threads = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    repeat = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    delay = float(sys.argv[7]) if len(sys.argv) > 7 else 0
    run_concurrent_clients(host, port, urlpath, directory, num_threads, repeat, delay)
