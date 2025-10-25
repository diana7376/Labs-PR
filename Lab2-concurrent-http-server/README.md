
# Lab 2: Concurrent HTTP File Server

## How to Run the Project

1. **Clone the repository (if you haven't):**

```sh
git clone https://github.com/diana7376/Labs-PR.git
cd Lab2-concurrent-http-server
```

2. **Build and run with Docker Compose**

```sh
docker-compose up --build
```

This launches the concurrent Python server (with `content/` shared) on [http://localhost:8000](http://localhost:8000).
3. **Access the app in your browser:**
Go to [http://localhost:8000](http://localhost:8000) to see the file server UI.
4. **To stop the server:**
Use `Ctrl+C` or run:

```sh
docker-compose down
```

5. **To test concurrency and race conditions:**
In a new terminal, run:

```sh
python test_single_server.py        # Single-threaded behavior
python test_race_condition.py       # Race condition demonstration
python test_rate_limit.py           # Tests for rate limiting (429)
```


***

## Project Structure

```
Lab2-concurrent-http-server/
├── content/
│   ├── index.html
│   ├── python_syntax.pdf
│   ├── files/
│   │   ├── docs/
│   │   └── photos/
│   │       ├── img.png
│   │       ├── img_1.png
│   │       └── ... (more images)
│   └── ... (more files)
├── concurrent_server.py
├── server.py
├── test_race_condition.py
├── test_rate_limit.py
├── test_single_server.py
├── docker-compose.yml
├── Dockerfile
└── README.md
```


***

## Step-by-Step Tutorial \& Results

### 1. File Server UI

When the server is running, visiting the root URL displays a clean, modern UI showing available images, PDFs, and directories. Each file displays an icon and a counter for download hits.

>![Home Page](content%2Ffiles%2Fphotos%2Fimg_7.png)
> *Figure 1: Home page of the HTTP file server, user-friendly and styled, sample files and counters visible.*

***

### 2. Testing Single vs Concurrent Server

#### **Single-threaded server**

- Only one request at a time: concurrent client requests are processed sequentially.
- Test output: High total time, low throughput.

>![img_3.png](content%2Ffiles%2Fphotos%2Fimg_3.png)
> *Figure 2: Single-threaded test—10 requests in ~10s, confirming sequential handling.*

#### **Concurrent server**

- Multiple requests handled in parallel via threads: much faster throughput.
- Test output: All requests finish in a much shorter time.

>![img_1.png](content%2Ffiles%2Fphotos%2Fimg_1.png)
> *Figure 3: Concurrent (multi-threaded) test—10 requests in ~2s, confirming parallel processing.*

***

### 3. Request Counter \& Race Condition

#### **Race condition (no locking)**

- The naive implementation lacks thread safety.
- Running the stress test reveals lost updates: the "actual count" is less than the number of requests.
- Race condition is visible both in the terminal and UI.


>![img_2.png](content%2Ffiles%2Fphotos%2Fimg_2.png)
> *Figure 4: Terminal output and UI show lost updates: actual file counter is wrong.*

#### **Thread-safe update (with locking)**

- `threading.Lock()` protects the counter variable.
- Counter always matches number of requests—no lost updates, race condition is solved.

>![img.png](content%2Ffiles%2Fphotos%2Fimg.png)
> *Figure 5: Counter matches requests: race condition solved with lock.*

---

## Race Condition Code from `concurrent_server.py`

### ❌ **NAIVE Implementation (Race Condition - NOT Thread-Safe)**

```python
def increment_file_counter_naive(self, filepath):
    """NAIVE implementation - NO LOCK - will cause race condition"""
    current = self.request_counter.get(filepath, 0)
    time.sleep(0.01)  # Simulates processing delay - makes race condition visible
    self.request_counter[filepath] = current + 1
    print(f"   [NAIVE] Thread {threading.current_thread().name}: "
          f"Read {current}, Writing {current + 1} for {os.path.basename(filepath)}")
```

**Problem:**
- Multiple threads read the same `current` value
- Each thread independently increments and writes back
- **Result:** Lost updates, incorrect counter values

***

### ✅ **THREAD-SAFE Implementation (Fixed with Lock)**

```python
def increment_file_counter_safe(self, filepath):
    """THREAD-SAFE implementation using lock"""
    with self.counter_lock:
        current = self.request_counter.get(filepath, 0)
        time.sleep(0.01)  # Simulates processing - but now protected by lock
        new_value = current + 1
        self.request_counter[filepath] = new_value
        print(f"   [SAFE] Thread {threading.current_thread().name}: "
              f"Read {current}, Writing {new_value} for {os.path.basename(filepath)}")
```

**Solution:**
- `with self.counter_lock:` ensures only ONE thread executes this block at a time
- Other threads wait until the lock is released
- **Result:** Every increment is counted correctly

***

### **Lock Initialization (in `__init__`)**

```python
class ConcurrentHTTPServer:
    def __init__(self, host='0.0.0.0', port=8000, document_root='content', 
                 use_thread_pool=True, max_workers=10):
        # ... other initialization ...
        
        # Request counter - will demonstrate race condition
        self.request_counter = {}
        self.counter_lock = threading.Lock()  # ← Lock to protect counter
        
        # Rate limiting - per IP tracking
        self.rate_limit_data = defaultdict(lambda: {'requests': [], 'blocked': 0})
        self.rate_limit_lock = threading.Lock()  # ← Lock for rate limiting
```

***

### **Usage in `serve_file` Method**

```python
def serve_file(self, requested_path):
    # ...
    try:
        if os.path.isfile(filepath):
            # UNCOMMENT THIS to see race condition:
            # self.increment_file_counter_naive(filepath)
            
            # THREAD-SAFE implementation (current):
            self.increment_file_counter_safe(filepath)
            
            return self.serve_single_file(filepath)
```

***

### **Additional Thread-Safe Operations**

Your code also demonstrates proper locking in other areas:

**1. Rate Limiting (Thread-Safe):**
```python
def check_rate_limit(self, client_ip):
    """Check if client IP has exceeded rate limit (thread-safe)"""
    with self.rate_limit_lock:
        current_time = time.time()
        client_data = self.rate_limit_data[client_ip]
        
        # Remove requests older than 1 second
        client_data['requests'] = [
            req_time for req_time in client_data['requests']
            if current_time - req_time < 1.0
        ]
        
        # Check if under rate limit
        if len(client_data['requests']) >= self.rate_limit:
            client_data['blocked'] += 1
            return False
        
        # Add current request
        client_data['requests'].append(current_time)
        return True
```

**2. Statistics Tracking (Thread-Safe):**
```python
def serve_stats_json(self):
    try:
        stats = {}
        with self.counter_lock:  # ← Protected read
            for filepath, count in self.request_counter.items():
                filename = os.path.basename(filepath)
                stats[filename] = count
        # ... rest of method
```
***

### 4. Rate Limiting (429 Too Many Requests)

#### **Burst requests (spammer):**

- Client spams too many requests quickly, most are blocked with HTTP 429.
- Only a few succeed.

>![img_4.png](content%2Ffiles%2Fphotos%2Fimg_4.png)
> *Figure 6: Burst spammer only gets through with a few requests, the rest are 429.*

#### **Good client (respects the limit):**

- Requests below/at the limit succeed with 200 OK and are not blocked.

>![img_5.png](content%2Ffiles%2Fphotos%2Fimg_5.png)
> *Figure 7: Good client succeeds with all requests at the allowed rate, 0% block rate.*

#### **Demonstrating Per-IP Rate Limiting and Concurrency Control**

The image below demonstrates how the server keeps track of client IP addresses and enforces rate limiting individually for each client. In this experiment, one client IP was used to make a large number of rapid, consecutive requests, quickly exceeding the maximum allowed requests per second and receiving HTTP 429 (Too Many Requests) responses, as seen in the terminal output/logs. At the same time, another client with a different IP address was able to continue sending requests successfully without being affected by the first client’s rate limiting status. This confirms that the server accurately distinguishes between clients based on their IP addresses and applies the rate limiting policy independently, ensuring fair access for all users and immunity to spam from a single IP.

![img_9.jpg](content%2Ffiles%2Fphotos%2Fimg_9.jpg)

#### **429 Error UI**

- When rate limit is hit, the user receives a stylish branded 429 page, matching the overall design.

>![img_6.png](content%2Ffiles%2Fphotos%2Fimg_6.png)
> *Figure 8: Custom 429 error page shows clear message and friendly UI.*

***

### 5. Server Logs and Stats

- Detailed logs are available showing request processing and any rate limit events.
- Real-time counter and stats are available via the `/stats` endpoint.

***


## Summary

- Project delivers all required functionality for Lab 2:
    - Concurrency with thread pool
    - Thread-safe counter (race-condition proof)
    - Polished UI \& icons
    - Correct rate-limiting
    - Dockerized, reproducible setup
- All code and results are **demonstrated step by step above**, with direct reference to your screenshots and output.

***