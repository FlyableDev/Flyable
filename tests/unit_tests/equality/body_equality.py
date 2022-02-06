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
Name: float_equality
Flyable-version: v0.1a1
Description: Test the equality between two floats
"""
# Flytest:start
print(15.12 == 15.12)
# Flytest:end


# Flytest:new
"""
Name: bool_equality
Flyable-version: v0.1a1
Description: Test the equality between two boolean
"""
# Flytest:start
print(False == False)
print(True == True)
print(False == True)
print(True == False)
# Flytest:end


# Flytest:new
"""
Name: triple_equality
Flyable-version: v0.1a1
Description: Test triple equality
"""
# Flytest:start
print(2 == 2 == 2)
# Flytest:end


# Flytest:new
"""
Name: is_operator
Flyable-version: v0.1a1
Description: Test the is operator
"""
# Flytest:start
print(True is True)
print(True is False)
print(False is False)
print(False is True)
# Flytest:end


# Flytest:new
"""
Name: zero_and_one_bool_comparison_with_is
Flyable-version: v0.1a1
Description: Test the equality between 0, 1 and booleans using is operator
"""
# Flytest:start
print(0 is False)
print(1 is False)
print(0 is True)
print(1 is True)
# Flytest:end


# Flytest:new
"""
Name: zero_and_one_bool_comparison_with_equal
Flyable-version: v0.1a1
Description: Test the equality between 0, 1 and boolean using equal operator
"""
# Flytest:start
print(0 == False)
print(1 == False)
print(0 == True)
print(1 == True)
# Flytest:end