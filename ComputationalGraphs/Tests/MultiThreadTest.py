import time
from concurrent.futures import ThreadPoolExecutor

# Pure Python matrix multiplication
def compute_python_matrix_multiplication(size, task_id):
    print(f"Task {task_id} started.")
    a = [[i + j for j in range(size)] for i in range(size)]
    b = [[i * j for j in range(size)] for i in range(size)]
    result = [[sum(a[i][k] * b[k][j] for k in range(size)) for j in range(size)] for i in range(size)]
    total_sum = sum(sum(row) for row in result)
    print(f"Task {task_id} finished.")
    return total_sum

# Single-threaded execution
def run_single_threaded(task_sizes):
    start_time = time.time()
    results = []
    for i, size in enumerate(task_sizes):
        results.append(compute_python_matrix_multiplication(size, i))
    end_time = time.time()
    return results, end_time - start_time

# Multi-threaded execution
def run_multi_threaded(task_sizes, max_workers=4):
    start_time = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(compute_python_matrix_multiplication, size, i) for i, size in enumerate(task_sizes)]
        for future in futures:
            results.append(future.result())
    end_time = time.time()
    return results, end_time - start_time

# Main function
def main():
    task_sizes = [300, 300, 300, 300 ,300 ,300, 300, 300, 300, 300, 300, 300, 300 ,300 ,300, 300]  # Increase size for more CPU usage

    print("Running in single-threaded mode...")
    single_threaded_results, single_threaded_time = run_single_threaded(task_sizes)
    print(f"Single-threaded results (sum of matrices): {single_threaded_results}")
    print(f"Single-threaded time: {single_threaded_time:.4f} seconds")

    print("\nRunning in multi-threaded mode...")
    multi_threaded_results, multi_threaded_time = run_multi_threaded(task_sizes, max_workers=8)
    print(f"Multi-threaded results (sum of matrices): {multi_threaded_results}")
    print(f"Multi-threaded time: {multi_threaded_time:.4f} seconds")

    # Compare performance
    speedup = single_threaded_time / multi_threaded_time
    print(f"\nSpeedup from parallelization: {speedup:.2f}x")

if __name__ == "__main__":
    main()
