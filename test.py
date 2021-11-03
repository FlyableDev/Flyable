import time


def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True


def main():
    start = time.time()
    primes = []
    for i in range(100_000):
        is_prime(i)
        
    print(time.time() - start, "seconds to find all the primes until 100_000")
    print("primes:", primes)


def t():
    print(4 % 10)


t()
input("Press <ENTER> to end the program...")