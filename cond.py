a = 10
b = 30
c = "test_cond"
d = "op"

result = ""

# Test the if true
if a == 10:
    result += "Y"


# Test the elif
if b == 1:
    result += "N"
elif b == 2:
    result += "N"
elif b == 30:
    result += "Y"


# Test the condition on python object
if c == d:
    result += "N"
else:
    result += "Y"


print(result)

