from concurrent.futures import ThreadPoolExecutor


def compute_python_matrix_multiplication(size, task_id):
    a = [[i + j for j in range(size)] for i in range(size)]
    b = [[i * j for j in range(size)] for i in range(size)]
    result = [
        [sum(a[i][k] * b[k][j] for k in range(size)) for j in range(size)]
        for i in range(size)
    ]
    return sum(sum(row) for row in result)


def run_single_threaded(task_sizes):
    results = []
    for i, size in enumerate(task_sizes):
        results.append(compute_python_matrix_multiplication(size, i))
    return results


def run_multi_threaded(task_sizes, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(compute_python_matrix_multiplication, size, i)
            for i, size in enumerate(task_sizes)
        ]
        return [future.result() for future in futures]


def test_multithreaded_matrix_multiplication_matches_single_threaded():
    task_sizes = [10, 10]
    single_results = run_single_threaded(task_sizes)
    multi_results = run_multi_threaded(task_sizes, max_workers=4)

    assert single_results == multi_results
