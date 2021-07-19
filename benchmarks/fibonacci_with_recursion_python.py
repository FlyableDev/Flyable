import time


def bench(n):
    if n <= 1:
        return n
    else:
        return bench(n - 1) + bench(n - 2)


begin = time.time()
a = bench(40)
end = time.time()
print(end - begin)
