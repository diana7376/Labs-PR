import requests
import time
import concurrent.futures
import subprocess
import json
import sys
import os

# --- Configuration ---
LEADER_URL = "http://localhost:8000"
KEYS = [f"test_key_{i}" for i in range(5)]
TEST_WRITES = 50
CONCURRENCY = 5


def send_write(i: int):
    """Sends a single write request and measures latency."""
    key = KEYS[i % len(KEYS)]
    # Value includes the write index for verification
    value = f"test_op_{i}"

    try:
        resp = requests.post(f"{LEADER_URL}/write", json={"key": key, "value": value}, timeout=10)
        resp.raise_for_status()  # Raise exception for 4xx or 5xx status codes
        return f"Write {i} success"
    except requests.exceptions.RequestException as e:
        return f"Write {i} failed: {e}"


def run_integration_test():
    """Runs concurrent writes to test the full system integration."""
    print("\n--- Starting Integration Test (Concurrent Writes) ---")

    successful_writes = 0

    # Use ThreadPoolExecutor to simulate concurrent clients
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        # Submit all tasks
        futures = [executor.submit(send_write, i) for i in range(TEST_WRITES)]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if "success" in result:
                successful_writes += 1
            # else: print(result) # Uncomment to see individual failures

    print(f"Integration Test Complete: {successful_writes} of {TEST_WRITES} writes succeeded.")
    return successful_writes == TEST_WRITES


def check_consistency():
    """Performs the integrity check: verifies all followers match the leader."""
    print("\n--- Starting Integrity Check (Data Consistency) ---")

    # 1. Get ground truth from the Leader
    try:
        leader_data = requests.get(f"{LEADER_URL}/data", timeout=5).json()
        print(f"Leader key count: {len(leader_data)}")
    except Exception as e:
        print(f"ERROR: Could not contact Leader at {LEADER_URL}. Is Docker running? Error: {e}")
        return False

    mismatches = 0

    # 2. Check all 5 followers (using their explicit container names)
    for i in range(1, 6):
        container_name = f"kv-follower-{i}"
        # Execute curl command inside the follower container
        cmd = f"docker exec {container_name} curl -s http://localhost:80/data"

        try:
            # Execute command and parse JSON result
            result = subprocess.check_output(cmd, shell=True, timeout=5).decode('utf-8')
            follower_data = json.loads(result)

            # 3. Verification
            if follower_data != leader_data:
                # Diagnostic printout: Check one of the keys to see the difference
                example_key = KEYS[0]
                leader_val = leader_data.get(example_key, 'N/A')
                follower_val = follower_data.get(example_key, 'N/A')

                print(
                    f"FAILURE: Follower {i} ({container_name}) MISMATCH. Key '{example_key}': Leader='{leader_val}' vs Follower='{follower_val}'.")
                mismatches += 1
            else:
                print(f"SUCCESS: Follower {i} ({container_name}) is consistent.")

        except Exception as e:
            print(f"ERROR: Failed to query Follower {i} via Docker. Check logs. Error: {e}")
            mismatches += 1

    if mismatches == 0:
        print("\nINTEGRITY CHECK PASSED: All nodes are fully consistent.")
        return True
    else:
        print(f"\nINTEGRITY CHECK FAILED: {mismatches} nodes out of sync.")
        return False


def main():
    # Ensure Docker is running and set up before running tests
    # NOTE: This script ASSUMES Docker is running from a previous `docker-compose up` command.

    # We need a stable wait time before the test starts
    print("Waiting 5 seconds for system stability...")
    time.sleep(5)

    # 1. Run the Integration Test
    integration_success = run_integration_test()

    # Wait for all background replication tasks to complete
    # CRITICAL FIX: Increased wait time to 5 seconds to account for the 1000ms maximum delay
    print("\nWaiting 5 seconds for eventual consistency convergence...")
    time.sleep(5)

    # 2. Run the Integrity Check
    integrity_success = check_consistency()

    if integration_success and integrity_success:
        print("\n--- SYSTEM TEST PASSED ---")
        sys.exit(0)
    else:
        print("\n--- SYSTEM TEST FAILED ---")
        sys.exit(1)


if __name__ == "__main__":
    main()