import requests
import threading
import random
import time

LEADER = "localhost:8000"  # Leader's API endpoint
NUM_WRITES = 100         # Total number of write operations
NUM_KEYS = 100             # Number of distinct keys
NUM_THREADS = 20           # Level of concurrency

def worker(writes):
    for _ in range(writes):
        key = f"key-{random.randint(1, NUM_KEYS)}"
        value = random.randint(1, 1000000)
        try:
            requests.post(f"http://{LEADER}/put/{key}", json={"value": value}, timeout=2)
        except Exception as e:
            print(f"Error writing {key}: {e}")

if __name__ == "__main__":
    threads = []
    start = time.time()
    writes_per_thread = NUM_WRITES // NUM_THREADS

    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(writes_per_thread,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    end = time.time()

    print(f"Total time for {NUM_WRITES} writes: {end - start:.2f} seconds")
    print(f"PERFORMANCE_RESULT {end - start:.2f}")
