"""Module where equality body tests are created"""

# Flytest:new
"""
Name: int_equality
Flyable-version: v0.1a1
Description: Test the equality between two integers
"""
# Flytest:start
print(15 == 15)
# Flytest:end


# Flytest:new
"""
Name: addition
Flyable-version: v0.1a1
Description: Test the addition operator
"""
# Flytest:start
print(0 + 0)
print(0 + 1)
print(1 + 1)
import sys
MAX_INT = sys.maxsize
print(MAX_INT + 0)
print(10000000000000 + 10000000000000)
# Flytest:end


# Flytest:new
"""
Name: substraction
Flyable-version: v0.1a1
Description: Test the subtraction operator
"""
# Flytest:start
print(0 - 0)
print(0 - 1)
print(1 - 0)
print(1 - 1)
import sys
MAX_INT = sys.maxsize
print(0 - MAX_INT)
print(51004 - 2414423)
# Flytest:end


# Flytest:new
"""
Name: multiplication
Flyable-version: v0.1a1
Description: Test the multiplication operator
"""
# Flytest:start

print(0 * 0)
print(5 * 0)
print(120 * 32)
print(50 * -50)
print(-50 * -50)
# Flytest:end


# Flytest:new
"""
Name: division
Flyable-version: v0.1a1
Description: Test the divide operator
"""
# Flytest:start
print(0 / 5)
print(1 / 10)
print(1 / 10.0)
print(50 / 50)
print(50.0 / 50)
print(50.0 / 50.0)
print(50 / -50)
print(-50 / -50)
# Flytest:end


# Flytest:new
"""
Name: division_by_zero
Flyable-version: v0.1a1
Description: Test the division by zero
"""
# Flytest:start
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
# Flytest:end


# Flytest:new
"""
Name: modulo
Flyable-version: v0.1a1
Description: Test the modulo operator
"""
# Flytest:start
print(0 % 2)
print(42 % 2)
print(3 % 2)
print(8 % 6)
print(8 % -6)
print(-8 % 6)
print(-8 % -6)
# Flytest:end


# Flytest:new
"""
Name: pow
Flyable-version: v0.1a1
Description: Test the pow operator
"""
# Flytest:start
print(1 ** 0)
print(16 ** 0)
print(-16 ** 0)
print(2 ** 8)
print(2 ** -8)
print(-2 ** 8)
print(-2 ** -8)
# Flytest:end


# Flytest:new
"""
Name: floor_division
Flyable-version: v0.1a1
Description: Test the pow operator
"""
# Flytest:start
print(0 // 5)
print(1 // 10)
print(1 // 10.0)
print(50 // 50)
print(40.0 // 50)
print(40.0 // 50.0)
print(40 // -50)
print(-40 // -50)
# Flytest:end
