import requests, threading, random, time

LEADER = "localhost:5000"
NUM_WRITES = 10000
NUM_KEYS = 100
NUM_THREADS = 20

def worker(writes):
    for _ in range(writes):
        key = f"key-{random.randint(1, NUM_KEYS)}"
        value = random.randint(1, 1000000)
        requests.post(f"http://{LEADER}/put/{key}", json={"value": value})

threads = []
start = time.time()
for _ in range(NUM_THREADS):
    t = threading.Thread(target=worker, args=(NUM_WRITES // NUM_THREADS,))
    t.start()
    threads.append(t)
for t in threads:
    t.join()
end = time.time()

print("Total time for", NUM_WRITES, "writes:", end - start)
