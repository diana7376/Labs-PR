import requests
import time
from concurrent.futures import ThreadPoolExecutor
import sys

SERVER_URL = "http://localhost:8000/index.html"
NUM_REQUESTS = 10
BATCH_SIZE = 5

print(f"Testing: {SERVER_URL}")
print(f"Making {NUM_REQUESTS} concurrent requests (batches of {BATCH_SIZE})...\n")


def make_request(request_id):
    try:
        response = requests.get(
            SERVER_URL,
            timeout=15,
            headers={'Connection': 'close'}
        )
        return {
            'id': request_id,
            'status': response.status_code,
            'success': response.status_code == 200
        }
    except Exception as e:
        print(f"  Request {request_id} failed: {type(e).__name__}")
        return {
            'id': request_id,
            'status': 'ERROR',
            'success': False
        }


start_time = time.time()
all_results = []

for batch_start in range(0, NUM_REQUESTS, BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE, NUM_REQUESTS)
    batch_ids = range(batch_start, batch_end)

    print(f"Processing requests {batch_start} to {batch_end - 1}...")

    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        futures = [executor.submit(make_request, i) for i in batch_ids]
        results = [future.result() for future in futures]
        all_results.extend(results)

    if batch_end < NUM_REQUESTS:
        time.sleep(0.1)

end_time = time.time()
total_time = end_time - start_time

successful = sum(1 for r in all_results if r['success'])
failed = NUM_REQUESTS - successful

print(f"\n Results:")
print(f"  Total time: {total_time:.3f} seconds")
print(f"  Successful: {successful}/{NUM_REQUESTS}")
print(f"  Failed: {failed}/{NUM_REQUESTS}")

if successful > 0:
    print(f"  Throughput: {successful / total_time:.2f} successful requests/second")

    if total_time < 5:
        print(f"\n Server is processing requests concurrently")
    else:
        print(f"\n  Server appears to be processing sequentially")

if successful == NUM_REQUESTS:
    print(f"\n All requests successful!")
