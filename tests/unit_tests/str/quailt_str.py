"""Module where str body tests are created"""

# Quail-test:new
"""
Name: empty_str_creation
Flyable-version: v0.1a1
Description: Test that the result of "" equals the result of calling str()
"""
# Quail-test:start
litteral_str = ""
litteral_str_by_method = str()
litteral_str == litteral_str_by_method  # Quail-assert: True
# print(litteral_str == litteral_str_by_method)
# Quail-test:end


# Quail-test:new
"""
Name: len_str
Flyable-version: v0.1a1
Description: Test that the len function works properly on strings
"""
# Quail-test:start
msg = "hello world!"
len(msg) == 12  # Quail-assert: True
msg2 = ""
len(msg2) == 1  # Quail-assert: False
len(msg2) == 0  # Quail-assert: True
# Quail-test:end


# Quail-test:new
"""
Name: concatenation
Flyable-version: v0.1a1
Description: Test the string concatenation functions
"""
# Quail-test:start
world = "World!"
"Hello " + world + " " + str(42)  # Quail-assert: eq 'Hello World! 42'
'Hello {} {}'.format(world, 42)  # Quail-assert: eq 'Hello World! 42'
f"Hello {world} "  # Quail-assert: eq 'Hello World! '
"%s %s %s" % ('Hello', world, 22)  # Quail-assert: eq 'Hello World! 22'
# Quail-test:end
