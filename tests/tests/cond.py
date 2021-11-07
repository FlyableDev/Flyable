a = 10
b = 30
c = "test_cond"
d = "op"

result = ""

# Test the if true
if a == 10:
    print("Y")


# Test the elif
if b == 1:
    print("N")
elif b == 2:
    print("N")
elif b == 30:
    print("Y")


# Test the condition on python object
if c == d:
    print("N")
else:
    print("Y")