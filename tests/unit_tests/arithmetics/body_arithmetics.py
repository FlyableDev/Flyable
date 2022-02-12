"""Module where equality body tests are created"""

# Quail-test:new
"""
Name: int_equality
Flyable-version: v0.1a1
Description: Test the equality between two integers
"""
# Quail-test:start
print(15 == 15)
# Quail-test:end


# Quail-test:new
"""
Name: addition
Flyable-version: v0.1a1
Description: Test the addition operator
"""
# Quail-test:start
0 + 0  # Quail-assert: eq 0
0 + 1  # Quail-assert: eq 1
1 + 1  # Quail-assert: eq 2
import sys

MAX_INT = sys.maxsize
MAX_INT + 0  # Quail-assert: eq MAX_INT
10000000000000 + 10000000000000   # Quail-assert: -
# Quail-test:end


# Quail-test:new
"""
Name: substraction
Flyable-version: v0.1a1
Description: Test the subtraction operator
"""
# Quail-test:start
print(0 - 0)
print(0 - 1)
print(1 - 0)
print(1 - 1)
import sys

MAX_INT = sys.maxsize
print(0 - MAX_INT)
print(51004 - 2414423)
# Quail-test:end


# Quail-test:new
"""
Name: multiplication
Flyable-version: v0.1a1
Description: Test the multiplication operator
"""
# Quail-test:start

print(0 * 0)
print(5 * 0)
print(120 * 32)
print(50 * -50)
print(-50 * -50)
# Quail-test:end


# Quail-test:new
"""
Name: division
Flyable-version: v0.1a1
Description: Test the divide operator
"""
# Quail-test:start
print(0 / 5)
print(1 / 10)
print(1 / 10.0)
print(50 / 50)
print(50.0 / 50)
print(50.0 / 50.0)
print(50 / -50)
print(-50 / -50)
# Quail-test:end


# Quail-test:new
"""
Name: division_by_zero
Flyable-version: v0.1a1
Description: Test the division by zero
"""
# Quail-test:start
try:
    print(5 / 0)
except ZeroDivisionError:
    print("Division by zero")
try:
    print(0 / 0)
except ZeroDivisionError:
    print("Division by zero")
try:
    print(2 % 0)
except ZeroDivisionError:
    print("Division by zero")
try:
    print(5 // 0)
except ZeroDivisionError:
    print("Division by zero")
# Quail-test:end


# Quail-test:new
"""
Name: modulo
Flyable-version: v0.1a1
Description: Test the modulo operator
"""
# Quail-test:start
print(0 % 2)
print(42 % 2)
print(3 % 2)
print(8 % 6)
print(8 % -6)
print(-8 % 6)
print(-8 % -6)
# Quail-test:end


# Quail-test:new
"""
Name: pow
Flyable-version: v0.1a1
Description: Test the pow operator
"""
# Quail-test:start
print(1 ** 0)
print(16 ** 0)
print(-16 ** 0)
print(2 ** 8)
print(2 ** -8)
print(-2 ** 8)
print(-2 ** -8)
# Quail-test:end


# Quail-test:new
"""
Name: floor_division
Flyable-version: v0.1a1
Description: Test the pow operator
"""
# Quail-test:start
print(0 // 5)
print(1 // 10)
print(1 // 10.0)
print(50 // 50)
print(40.0 // 50)
print(40.0 // 50.0)
print(40 // -50)
print(-40 // -50)
# Quail-test:end
