import matplotlib.pyplot as plt

quorums = [1,2,3,4,5]
avg_latencies = []

for quorum in quorums:
    # set quorum in docker-compose, restart
    # run integration test, collect avg latency
    avg_latencies.append(measured_latency)

plt.plot(quorums, avg_latencies)
plt.xlabel('Write Quorum')
plt.ylabel('Average Write Latency')
plt.title('Write Quorum vs Average Latency')
plt.show()
