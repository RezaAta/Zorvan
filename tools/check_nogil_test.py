import os
import sys
import threading
import time
from multiprocessing import Process

print("sys.version:", sys.version)
print("executable:", sys.executable)
print("cpu_count:", os.cpu_count())


def busy(n):
    s = 0
    for i in range(n):
        s += i * i
    return s


def run_threads(num_threads, iterations):
    threads = []
    start = time.time()
    for _ in range(num_threads):
        th = threading.Thread(target=busy, args=(iterations,))
        th.start()
        threads.append(th)
    for th in threads:
        th.join()
    return time.time() - start


def run_processes(num_processes, iterations):
    procs = []
    start = time.time()
    for _ in range(num_processes):
        p = Process(target=busy, args=(iterations,))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    return time.time() - start


if __name__ == "__main__":
    iters = 10_000_000
    print("\n-- Thread test (CPU-bound) --")
    for n in (1, 2, 4):
        t = run_threads(n, iters // n)
        print(f"threads={n}, time={t:.3f}s")

    print("\n-- Process test (CPU-bound) --")
    for n in (1, 2, 4):
        t = run_processes(n, iters // n)
        print(f"processes={n}, time={t:.3f}s")
