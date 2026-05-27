from flask import Flask, jsonify
import threading
import time
import random
import psutil
from collections import deque

app = Flask(__name__)

simulated_load = 0
active_requests = 0
load_history = deque(maxlen=10)
cpu_history = deque(maxlen=15)
lock = threading.Lock()


def simulated_request_worker(request_id: int):
    global simulated_load
    global active_requests

    # random processing time between 3 and 8 seconds
    processing_time = random.randint(3, 8)

    # random load increment between 4% and 10%
    load_increment = random.randint(4, 10)

    with lock:
        active_requests += 1
        simulated_load = min(simulated_load + load_increment, 100)

    print(
        f"[REQUEST {request_id}] START | "
        f"+{load_increment}% load | "
        f"processing {processing_time}s"
    )

    # wait for the simulated processing time
    time.sleep(processing_time)

    # gradually reduce the load over 3 to 6 seconds
    reduction_steps = random.randint(3, 6)
    reduction_amount = load_increment / reduction_steps

    for _ in range(reduction_steps):
        time.sleep(1)

        with lock:
            simulated_load = max(
                simulated_load - reduction_amount,
                0
            )

    with lock:
        active_requests -= 1

    print(f"[REQUEST {request_id}] END")


def traffic_generator():
    request_counter = 0

    while True:
        wait_time = random.randint(1, 10)
        
        requests_count = random.randint(1, 3)

        print(
            f"\n[TRAFFIC] "
            f"{requests_count} simulated requests "
            f"in {wait_time}s"
        )

        time.sleep(wait_time)

        for _ in range(requests_count):
            request_counter += 1

            threading.Thread(
                target=simulated_request_worker,
                args=(request_counter,),
                daemon=True
            ).start()

def metrics_smoother():
    global simulated_load

    while True:
        with lock:
            load_history.append(simulated_load)

        time.sleep(1)


@app.route("/metrics")
def metrics():

    #realtime metrics
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_history.append(cpu_percent)
    memory = psutil.virtual_memory()

    with lock:
        current_load = round(simulated_load, 2)
        current_requests = active_requests

    average_load = (
        round(sum(load_history) / len(load_history), 2)
        if load_history else current_load
    )

    # Every active request adds to the effective load
    requests_factor = min(current_requests * 3, 100)

    
    average_cpu = (
    round(sum(cpu_history) / len(cpu_history), 2)
    if cpu_history else cpu_percent
    )
     # CPU acts as the baseline floor
    base_cpu = average_cpu

    # Simulated load moves the scaling pressure
    simulated_pressure = (
        (0.80 * average_load) +
        (0.20 * requests_factor)
    )
    effective_load = (
        base_cpu +
        simulated_pressure
    )
    effective_load = round(
        min(max(effective_load, 0), 100),
        2
    )
    
# JSON response with all metrics
    return jsonify({
        "status": "healthy",

        "cpu_percent": base_cpu,
        "ram_percent": memory.percent,
        "ram_used_mb": round(memory.used / 1024 / 1024, 2),

        "load_percent": average_load,
        "active_requests": current_requests,

        "effective_load_percent": effective_load,
        "timestamp": time.time()
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "alive"
    })

if __name__ == "__main__":

    print("Starting simulated workload system...")

    # traffic generator
    threading.Thread(
        target=traffic_generator,
        daemon=True
    ).start()

    # metrics smoother
    threading.Thread(
        target=metrics_smoother,
        daemon=True
    ).start()

    # Flask app
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )