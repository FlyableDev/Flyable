
def test_fibonacci(compiled_value):
    def fibonacci(n):
        if n <= 1:
            return n
        else:
            return fibonacci(n - 1) + fibonacci(n - 2)
    assert fibonacci(10) == compiled_value

