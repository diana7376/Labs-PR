import requests
import time
from concurrent.futures import ThreadPoolExecutor

SERVER_URL = "http://localhost:8000/python_syntax.pdf"


def make_request(request_id, client_name):
    try:
        response = requests.get(SERVER_URL, timeout=5, headers={'Connection': 'close'})
        status = response.status_code

        if status == 200:
            print(f"[{client_name}] Request {request_id:2d}: SUCCESS (200)")
        elif status == 429:
            print(f"[{client_name}] Request {request_id:2d}: RATE LIMITED (429)")
        else:
            print(f"[{client_name}] Request {request_id:2d}: ERROR ({status})")

        return {'id': request_id, 'status': status, 'success': status == 200, 'blocked': status == 429}

    except Exception as e:
        print(f"[{client_name}] Request {request_id:2d}: EXCEPTION ({type(e).__name__})")
        return {'id': request_id, 'status': 'ERROR', 'success': False, 'blocked': False}


def test_spammer():
    print("\n" + "=" * 70)
    print("TEST 1: SPAMMER - Sending 20 requests in a burst")
    print("=" * 70)

    start_time = time.time()

    # Send all 20 requests concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request, i, "SPAMMER") for i in range(1, 21)]
        results = [f.result() for f in futures]

    end_time = time.time()
    duration = end_time - start_time

    # Calculate statistics
    successful = sum(1 for r in results if r['success'])
    blocked = sum(1 for r in results if r['blocked'])
    errors = sum(1 for r in results if not r['success'] and not r['blocked'])

    print(f"\n--- SPAMMER Results ---")
    print(f"Total requests: 20")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Successful (200): {successful}")
    print(f"Blocked (429): {blocked}")
    print(f"Errors: {errors}")
    print(f"Success rate: {(successful / 20) * 100:.1f}%")
    print(f"Block rate: {(blocked / 20) * 100:.1f}%")

    return successful, blocked


def test_good_client():
    print("\n" + "=" * 70)
    print("TEST 2: GOOD CLIENT - Sending 5 requests at exactly 5 req/s")
    print("=" * 70)

    results = []
    start_time = time.time()

    for i in range(1, 6):
        result = make_request(i, "GOOD_CLIENT")
        results.append(result)

        if i < 5:
            time.sleep(0.2)

    end_time = time.time()
    duration = end_time - start_time

    successful = sum(1 for r in results if r['success'])
    blocked = sum(1 for r in results if r['blocked'])
    errors = sum(1 for r in results if not r['success'] and not r['blocked'])

    print(f"\n--- GOOD CLIENT Results ---")
    print(f"Total requests: 5")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Successful (200): {successful}")
    print(f"Blocked (429): {blocked}")
    print(f"Errors: {errors}")
    print(f"Success rate: {(successful / 5) * 100:.1f}%")
    print(f"Block rate: {(blocked / 5) * 100:.1f}%")

    return successful, blocked


def main():
    print("\n" + "=" * 70)
    print("RATE LIMITING TEST")
    print("=" * 70)
    print(f"Server: {SERVER_URL}")
    print(f"Rate limit: 5 requests/second per IP")
    print("=" * 70)

    spam_success, spam_blocked = test_spammer()

    print("\nWaiting 2 seconds for rate limiter to reset...")
    time.sleep(2)

    good_success, good_blocked = test_good_client()

    print("\n" + "=" * 70)
    print("FINAL COMPARISON")
    print("=" * 70)
    print(f"\nSPAMMER (burst of 20 requests):")
    print(f"Successful: {spam_success}/20 ({(spam_success / 20) * 100:.0f}%)")
    print(f"Blocked: {spam_blocked}/20 ({(spam_blocked / 20) * 100:.0f}%)")

    print(f"\nGOOD CLIENT (5 requests at 5 req/s):")
    print(f"Successful: {good_success}/5 ({(good_success / 5) * 100:.0f}%)")
    print(f"Blocked: {good_blocked}/5 ({(good_blocked / 5) * 100:.0f}%)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
