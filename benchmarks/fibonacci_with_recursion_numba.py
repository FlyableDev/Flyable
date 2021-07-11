from numba import jit
@jit
def benchmark(n):
    if n == 1:
        return 0
    elif n == 2:
        return 1
    else:
        return benchmark(n - 1)+benchmark(n - 2)
