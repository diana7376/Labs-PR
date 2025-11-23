import subprocess
import yaml
import matplotlib.pyplot as plt
import time

# Define the quorum values to test
quorums = [1, 2, 3, 4, 5]
avg_latencies = []

def update_write_quorum(quorum):
    # Edit docker-compose.yml to set WRITEQUORUM
    with open('docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)
    compose['services']['leader']['environment'] = [
        env if not env.startswith('WRITEQUORUM=') else f'WRITEQUORUM={quorum}'
        for env in compose['services']['leader']['environment']
    ]
    with open('docker-compose.yml', 'w') as f:
        yaml.dump(compose, f)

def run_performance_test():
    # Run integration test and parse total time
    result = subprocess.run(['python3', 'test_integration.py'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if line.startswith("PERFORMANCE_RESULT"):
            total_time = float(line.split()[1])
            return total_time
    return None


for quorum in quorums:
    print(f"\nTesting WRITEQUORUM={quorum} ...")
    update_write_quorum(quorum)
    # Restart the containers for the new quorum value
    subprocess.run(['docker-compose', 'down'])
    subprocess.run(['docker-compose', 'up', '-d'])  # run in detached mode
    time.sleep(7) # wait for servers to come up
    latency = run_performance_test()
    if latency:
        avg_latencies.append(latency)
        print(f"Average latency for quorum {quorum}: {latency:.2f} sec")
    else:
        avg_latencies.append(None)
    subprocess.run(['docker-compose', 'down'])  # stop containers before next run

print("Quorums tested:", quorums)
print("Latencies recorded:", avg_latencies)

# Plot results
plt.plot(quorums, avg_latencies, marker='o')
plt.xlabel('Write Quorum')
plt.ylabel('Total Write Latency (sec)')
plt.title('Write Quorum vs. Total Write Latency')
plt.grid()
plt.show()
