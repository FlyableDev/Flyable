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
    nb = 100000
    for i in range(nb):
        is_p = is_prime(i)
        if is_p:
            primes.append(i)
    print("primes:", primes)
    print(time.time() - start, "seconds to find all the primes until", nb)
    input("Press <ENTER> to end the program...")
    
main()
#a = 11
#b = 2
#print(a + b)
#print(a - b)
#print(a % b)
#print(a / b)
#print("hello " + "world!")

#input("Press <ENTER> to end the program...")