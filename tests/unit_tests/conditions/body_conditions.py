"""Module where conditions body tests are created"""

# Quail-test:new
"""
Name: if_statement
Flyable-version: v0.1a1
Description: Test that the if statement works properly
"""
# Quail-test:start
my_val = ""
if True:
    print(1)
# Quail-test:end


# Quail-test:new
"""
Name: if_else_statement
Flyable-version: v0.1a1
Description: Test that the if else statement works properly
"""
# Quail-test:start
if False:
    False  # Quail-assert: -
else:
    True  # Quail-assert: -
# Quail-test:end


# Quail-test:new
"""
Name: if_elif_statement
Flyable-version: v0.1a1
Description: Test that the if elif statement works properly
"""
# Quail-test:start
if False:
    print(1)
elif False:
    print(2)
# Quail-test:end


# Quail-test:new
"""
Name: if_elif_else_statement
Flyable-version: v0.1a1
Description: Test that the if elif and else statement work properly
"""
# Quail-test:start
if False:
    print(1)
elif False:
    print(2)
else:
    print(3)
# Quail-test:end
