"""Module where conditions body tests are created"""

# Flytest:new
"""
Name: if_statement
Flyable-version: v0.1a1
Description: Test that the if statement works properly
"""
# Flytest:start
my_val = ""
if True:
    print(1)
# Flytest:end


# Flytest:new
"""
Name: if_else_statement
Flyable-version: v0.1a1
Description: Test that the if else statement works properly
"""
# Flytest:start
if False:
    print(1)
else:
    print(2)
# Flytest:end


# Flytest:new
"""
Name: if_elif_statement
Flyable-version: v0.1a1
Description: Test that the if elif statement works properly
"""
# Flytest:start
if False:
    print(1)
elif False:
    print(2)
# Flytest:end


# Flytest:new
"""
Name: if_elif_else_statement
Flyable-version: v0.1a1
Description: Test that the if elif and else statement work properly
"""
# Flytest:start
if False:
    print(1)
elif False:
    print(2)
else:
    print(3)
# Flytest:end