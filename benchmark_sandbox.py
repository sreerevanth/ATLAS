import time
import psutil
import statistics
import sys
import platform
import random
import threading
from multiprocessing import Process, Queue

# Mock function for legitimate proof with variance
def legitimate_proof():
    x = 0
    # Simulate topology variance that changes proof length
    iters = random.randint(80, 120) 
    for i in range(iters):
        x += i * i
    return True

# Mock function for infinite loop
def infinite_loop():
    while True:
        pass

# Mock function for recursion bomb
def recursion_bomb():
    def recurse():
        return recurse()
    recurse()

# Mock function for memory bomb
def memory_bomb():
    arr = []
    while True:
        arr.append("A" * 1024 * 1024)

class BenchmarkFuelMeter:
    def __init__(self, max_fuel):
        self.max_fuel = max_fuel
        self.consumed_fuel = 0

    def trace_execution(self, frame, event, arg):
        if event == 'call':
            frame.f_trace_opcodes = True
            return self.trace_execution
        elif event == 'opcode':
            self.consumed_fuel += 1
            if self.consumed_fuel > self.max_fuel:
                raise Exception(f"Halted! Max fuel ({self.max_fuel}) reached.")
        return self.trace_execution

def sandbox_worker(target_func, max_fuel, q):
    import sys
    sys.setrecursionlimit(5000)
    meter = BenchmarkFuelMeter(max_fuel)
    sys.settrace(meter.trace_execution)
    
    start_time = time.time()
    try:
        target_func()
        q.put(("SUCCESS", meter.consumed_fuel, time.time() - start_time))
    except Exception as e:
        q.put(("BLOCKED", meter.consumed_fuel, time.time() - start_time))
    finally:
        sys.settrace(None)

def run_test(target_func, max_fuel, timeout=2.0):
    q = Queue()
    p = Process(target=sandbox_worker, args=(target_func, max_fuel, q))
    p.start()
    p.join(timeout)
    
    if p.is_alive():
        p.terminate()
        p.join()
        return ("TIMEOUT", max_fuel, timeout)
    
    if not q.empty():
        return q.get()
    return ("CRASH", 0, 0)

if __name__ == '__main__':
    print(f"=== EXPERIMENTAL METHODOLOGY ===")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Processor: {platform.processor()}")
    print(f"RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    
    NUM_RUNS = 1000
    print(f"\nStarting Adversarial Benchmark Suite ({NUM_RUNS} Iterations)...")
    
    legit_fuels = []
    for _ in range(NUM_RUNS):
        res, fuel, t = run_test(legitimate_proof, 500000)
        if res == "SUCCESS":
            legit_fuels.append(fuel)
    
    mean_legit = statistics.mean(legit_fuels) if legit_fuels else 0
    std_legit = statistics.stdev(legit_fuels) if len(legit_fuels) > 1 else 0
    
    # 3-Sigma Rule (99.7% confidence) + fixed bounds
    safe_upper_bound = int(mean_legit + (3 * std_legit))
    print(f"Legitimate Proofs: Mean Fuel: {mean_legit:.1f} (StDev: {std_legit:.1f})")
    print(f"Statistically Derived 3-Sigma Fuel Limit: {safe_upper_bound} opcodes")
    
    # 2. Infinite Loop DoS
    loop_blocked = 0
    for _ in range(NUM_RUNS):
        res, fuel, t = run_test(infinite_loop, safe_upper_bound)
        if res == "BLOCKED":
            loop_blocked += 1
    print(f"Infinite Loops: {loop_blocked/NUM_RUNS*100}% Blocked")
    
    # 3. Recursion Bombs
    rec_blocked = 0
    for _ in range(NUM_RUNS):
        res, fuel, t = run_test(recursion_bomb, safe_upper_bound)
        if res == "CRASH" or res == "BLOCKED": # Recursion hits python limit or our fuel
            rec_blocked += 1
    print(f"Recursion Bombs: {rec_blocked/NUM_RUNS*100}% Blocked")

    # 4. Memory Bombs
    mem_blocked = 0
    for _ in range(NUM_RUNS):
        res, fuel, t = run_test(memory_bomb, safe_upper_bound)
        if res == "BLOCKED" or res == "CRASH" or res == "TIMEOUT":
            mem_blocked += 1
    print(f"Memory Bombs: {mem_blocked/NUM_RUNS*100}% Blocked")
    
    print("\nBenchmark Complete. Updating Report Data.")
