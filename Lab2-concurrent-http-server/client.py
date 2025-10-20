import sys
import os
import requests
import threading
import time
from urllib.parse import urljoin

def save_file(content, directory, filename):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, filename), "wb") as f:
        f.write(content)

def handle_response(resp, save_dir, urlpath):
    content_type = resp.headers.get("Content-Type", "")
    filename = urlpath.strip("/").split("/")[-1] or "index.html"
    if "text/html" in content_type:
        print(resp.text)
    elif "png" in content_type or "pdf" in content_type:
        save_file(resp.content, save_dir, filename)
        print(f"Saved {filename} to {save_dir}")
    else:
        print(f"Unknown content type: {content_type}\n{resp.text}")

def client_thread(host, port, urlpath, directory, repeat=1, delay=0):
    url = f"http://{host}:{port}/{urlpath.lstrip('/')}"
    for _ in range(repeat):
        try:
            resp = requests.get(url)
            print(f"[{threading.current_thread().name}] {resp.status_code} {url}")
            handle_response(resp, directory, urlpath)
            time.sleep(delay)
        except Exception as e:
            print(f"[{threading.current_thread().name}] Error: {e}")

def run_concurrent_clients(host, port, urlpath, directory, num_threads=10, repeat=1, delay=0):
    threads = []
    start = time.time()
    for i in range(num_threads):
        t = threading.Thread(target=client_thread, args=(host, port, urlpath, directory, repeat, delay), name=f"Client-{i+1}")
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print(f"All clients finished in {time.time() - start:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python client.py serverhost serverport urlpath directory [num_threads] [repeat] [delay]")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    urlpath = sys.argv[3]
    directory = sys.argv[4]
    num_threads = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    repeat = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    delay = float(sys.argv[7]) if len(sys.argv) > 7 else 0
    run_concurrent_clients(host, port, urlpath, directory, num_threads, repeat, delay)
