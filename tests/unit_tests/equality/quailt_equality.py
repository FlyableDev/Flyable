"""Module where equality body tests are created"""

# Quail-test:new
"""
Name: int_equality
Flyable-version: v0.1a1
Description: Test the equality between two integers
"""
# Quail-test:start
15 == 15  # Quail-assert:True
# Quail-test:end


# Quail-test:new
"""
Name: float_equality
Flyable-version: v0.1a1
Description: Test the equality between two floats
"""
# Quail-test:start
print(15.12 == 15.12)
# Quail-test:end


# Quail-test:new
"""
Name: bool_equality
Flyable-version: v0.1a1
Description: Test the equality between two boolean
Dependencies: substraction, division
"""
# Quail-test:start
False == False  # Quail-assert: True
True == True    # Quail-assert: True
False == True   # Quail-assert: False
True == False   # Quail-assert: False
# Quail-test:end


# Quail-test:new
"""
Name: triple_equality
Flyable-version: v0.1a1
Description: Test triple equality
"""
# Quail-test:start
2 == 2 == 2  # Quail-assert: True
# Quail-test:end


# Quail-test:new
"""
Name: is_operator
Flyable-version: v0.1a1
Description: Test the is operator
"""
# Quail-test:start
print(True is True)
print(True is False)
print(False is False)
print(False is True)
# Quail-test:end


# Quail-test:new
"""
Name: zero_and_one_bool_comparison_with_is
Flyable-version: v0.1a1
Description: Test the equality between 0, 1 and booleans using is operator
"""
# Quail-test:start
print(0 is False)
print(1 is False)
print(0 is True)
print(1 is True)
# Quail-test:end


# Quail-test:new
"""
Name: zero_and_one_bool_comparison_with_equal
Flyable-version: v0.1a1
Description: Test the equality between 0, 1 and boolean using equal operator
"""
# Quail-test:start
print(0 == False)
print(1 == False)
print(0 == True)
print(1 == True)
# Quail-test:end
