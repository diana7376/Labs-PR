import subprocess
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = "8080"
URL_PATH = "/"  # or any path you want to test
DIRECTORY = "test_downloads"
REPEAT = 20    # total requests to send (per thread)
NUM_THREADS_SINGLE = 1
NUM_THREADS_MULTI = 10

def run_client(num_threads, repeat):
    args = [
        "python",
        "client.py",
        SERVER_HOST,
        SERVER_PORT,
        URL_PATH,
        DIRECTORY,
        str(num_threads),
        str(repeat),
        "0"  # No delay for max load
    ]
    print(f"\nRunning client.py with {num_threads} thread(s), {repeat} requests...")
    start = time.time()
    subprocess.run(args)
    end = time.time()
    return end - start

if __name__ == "__main__":
    print("=== Single-Threaded Test ===")
    time_single = run_client(NUM_THREADS_SINGLE, REPEAT)
    print(f"Single-threaded total time: {time_single:.2f} seconds")

    print("\n=== Multi-Threaded Test ===")
    time_multi = run_client(NUM_THREADS_MULTI, REPEAT)
    print(f"Multi-threaded total time: {time_multi:.2f} seconds")

    print("\n=== PERFORMANCE COMPARISON ===")
    print(f"Single-threaded: {time_single:.2f} seconds, Multi-threaded: {time_multi:.2f} seconds")
    if time_multi < time_single:
        print("Multi-threaded performance is faster as expected!")
    else:
        print("Single-threaded is faster (check server implementation for bottlenecks)!")
