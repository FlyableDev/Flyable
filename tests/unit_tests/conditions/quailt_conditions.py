"""Module where conditions body tests are created"""

# Quail-test:new
"""
Name: if_statement
Flyable-version: v0.1a1
Description: Test that the if statement works properly
"""
# Quail-test:start
x = 0
if True:
    x = 1

x # Quail-assert: eq 1

x = 0
if False:
    x = 1

x # Quail-assert: eq 0
# Quail-test:end


# Quail-test:new
"""
Name: if_else_statement
Flyable-version: v0.1a1
Description: Test that the if else statement works properly
"""
# Quail-test:start
x = 0
if False:
    x = 1
else:
    x = 2
x # Quail-assert: eq 2

x = 0
if True:
    x = 1
else:
    x = 2

x # Quail-assert: eq 1
# Quail-test:end


# Quail-test:new
"""
Name: if_elif_statement
Flyable-version: v0.1a1
Description: Test that the if elif statement works properly
"""
# Quail-test:start
x = 0
if False:
    x = 1
elif False:
    x = 2

x # Quail-assert: eq 0

x = 0
if False:
    x = 1
elif True:
    x = 2

x # Quail-assert: eq 2

x = 0
if True:
    x = 1
elif True:
    x = 2

x # Quail-assert: eq 1

x = 0
if True:
    x = 1
elif False:
    x = 2

x # Quail-assert: eq 1
# Quail-test:end


# Quail-test:new
"""
Name: if_elif_else_statement
Flyable-version: v0.1a1
Description: Test that the if elif and else statement work properly
"""
# Quail-test:start
x = 0
if False:
    x = 1
elif False:
    x = 2
else:
    x = 3

x # Quail-assert: eq 3

# Quail-test:end


# Quail-test:new
"""
Name: or_operator
Flyable-version: v0.1a1
Description: Test the or operator
"""
# Quail-test:start
True or False # Quail-assert: eq True
False or True # Quail-assert: eq True
True or True # Quail-assert: eq True
False or False # Quail-assert: eq False
# Quail-test:end


# Quail-test:new
"""
Name: and_operator
Flyable-version: v0.1a1
Description: Test the and operator
"""
# Quail-test:start
True and True # Quail-assert: eq True
True and False # Quail-assert: eq False
False and True # Quail-assert: eq False
False and False # Quail-assert: eq False
# Quail-test:end


# quail-test:new
"""
name: less_than
flyable-version: v0.1a1
description: test the less than operator (<)
"""
# quail-test:start
10 < 30 # quail-assert: eq True
-1 < 0 # quail-assert: eq True
-5 < -1 # quail-assert: eq True
-5 < -5 # quail-assert: eq False
5 < -5 # quail-assert: eq False
# quail-test:end


# quail-test:new
"""
name: less_than_equal
flyable-version: v0.1a1
description: test the less than or equal operator (<=)
"""
# quail-test:start
10 <= 30 # quail-assert: eq True
-1 <= 0 # quail-assert: eq True
-5 <= -1 # quail-assert: eq True
-5 <= -5 # quail-assert: eq True
5 <= 5 # quail-assert: eq True
5 <= -5 # quail-assert: eq False
# quail-test:end


# quail-test:new
"""
name: greater_than
flyable-version: v0.1a1
description: test the greater than operator (>)
"""
# quail-test:start
30 > 10 # quail-assert: eq True
0 > -1 # quail-assert: eq True
-1 > -5 # quail-assert: eq True
-5 > -5 # quail-assert: eq False
-5 > 5 # quail-assert: eq False
# quail-test:end


# quail-test:new
"""
name: greater_than_equal
flyable-version: v0.1a1
description: test the greater than or equal operator (>=)
"""
# quail-test:start
30 >= 10 # quail-assert: eq True
0 >= -1 # quail-assert: eq True
-1 >= -5 # quail-assert: eq True
-5 >= -5 # quail-assert: eq True
5 >= 5 # quail-assert: eq True
-5 >= 5 # quail-assert: eq False
# quail-test:end
