import requests
import sys
import time
from concurrent.futures import ThreadPoolExecutor


def make_request(url, index):
    try:
        requests.get(url, timeout=10, headers={'Connection': 'close'})
        return True
    except:
        return False


URL = "http://localhost:8000/python_syntax.pdf"
NUM_REQUESTS = int(sys.argv[1]) if len(sys.argv) > 1 else 50

print(f"Making {NUM_REQUESTS} concurrent requests to {URL}...")
print("=" * 60)

start = time.time()
with ThreadPoolExecutor(max_workers=NUM_REQUESTS) as executor:
    futures = [executor.submit(make_request, URL, i) for i in range(NUM_REQUESTS)]
    results = [f.result() for f in futures]
end = time.time()

successful = sum(results)

print(f"Completed in {end - start:.2f} seconds")
print(f"Successful requests: {successful}/{NUM_REQUESTS}")

time.sleep(0.3)

try:
    stats = requests.get('http://localhost:8000/stats').json()
    actual_count = stats.get('python_syntax.pdf', 0)

    print(f"\n Counter Results:")
    print(f"  Expected count: {successful}")
    print(f"  Actual count:   {actual_count}")

    if actual_count == successful:
        print(f"   CORRECT - No race condition!")
    else:
        print(f"   RACE CONDITION DETECTED!")
        print(f"     Lost {successful - actual_count} updates")
except Exception as e:
    print(f"Could not fetch stats: {e}")

print("=" * 60)