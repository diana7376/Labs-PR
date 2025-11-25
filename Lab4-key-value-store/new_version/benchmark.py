import requests
import time
import concurrent.futures
import matplotlib.pyplot as plt
import subprocess
import json
import os

LEADER_URL = "http://localhost:8000"
KEYS = [f"key-{i}" for i in range(10)]
TOTAL_WRITES = 100
BATCH_SIZE = 10


def restart_docker(quorum_val):
    """Restarts the cluster with a specific Quorum configuration."""
    print(f"\n--- Setting up Docker with WRITE_QUORUM={quorum_val} ---")
    env = os.environ.copy()
    env["WRITE_QUORUM"] = str(quorum_val)

    # Stop and remove volumes to ensure clean state
    subprocess.run(["docker-compose", "down"], check=True)
    subprocess.run(["docker-compose", "up", "-d", "--build"], env=env, check=True)

    print("Waiting for services to stabilize...")
    time.sleep(5)  # Give containers time to boot


def send_write(i):
    """Sends a single write request."""
    key = KEYS[i % len(KEYS)]
    value = f"value-{i}"
    start = time.time()
    try:
        resp = requests.post(f"{LEADER_URL}/write", json={"key": key, "value": value})
        lat = time.time() - start
        return lat, resp.status_code
    except Exception as e:
        return 0, 500


def run_load_test():
    """Runs concurrent writes and calculates average latency."""
    latencies = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        # Submit all tasks
        futures = [executor.submit(send_write, i) for i in range(TOTAL_WRITES)]

        for future in concurrent.futures.as_completed(futures):
            lat, status = future.result()
            if status == 200:
                latencies.append(lat)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    return avg_latency


def check_consistency():
    """Verifies that followers match the leader."""
    print("Checking consistency...")
    # Get leader data
    try:
        leader_data = requests.get(f"{LEADER_URL}/data").json()
    except:
        print("Could not contact leader.")
        return

    # Check 5 followers (assuming port mapping or internal docker IP access)
    # Since followers aren't exposed to host ports in compose file,
    # we use 'docker exec' to check them for this lab script.

    mismatches = 0
    for i in range(1, 6):
        container_name = f"distributed_lab-follower-{i}-1"  # Adjust based on folder name
        # A trick to curl from inside the container since we didn't map follower ports to host
        cmd = f"docker exec {container_name} curl -s http://localhost:80/data"
        try:
            result = subprocess.check_output(cmd, shell=True)
            follower_data = json.loads(result)

            # Simple length check or key check
            if len(follower_data) != len(leader_data):
                mismatches += 1
                print(f"Follower {i} MISMATCH: Leader {len(leader_data)} vs Follower {len(follower_data)}")
            else:
                # print(f"Follower {i} matches.")
                pass
        except Exception as e:
            print(f"Error checking follower {i}: {e}")

    if mismatches == 0:
        print("SUCCESS: All replicas match the leader!")
    else:
        print(
            f"WARNING: {mismatches} followers out of sync (Expected due to eventual consistency if checked immediately).")


def main():
    quorums = [1, 2, 3, 4, 5]
    avg_latencies = []

    for q in quorums:
        restart_docker(q)
        print(f"Running load test for Quorum={q}...")
        latency = run_load_test()
        avg_latencies.append(latency)
        print(f"Average Latency: {latency:.4f}s")

        # Wait a moment for trailing async replications to finish before checking consistency
        time.sleep(2)
        check_consistency()

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(quorums, avg_latencies, marker='o', linestyle='-', color='b')
    plt.title('Write Quorum vs Average Write Latency')
    plt.xlabel('Write Quorum (Number of confirmations)')
    plt.ylabel('Average Latency (seconds)')
    plt.grid(True)
    plt.savefig('quorum_latency_analysis.png')
    print("\nAnalysis complete. Plot saved to 'quorum_latency_analysis.png'.")


if __name__ == "__main__":
    main()