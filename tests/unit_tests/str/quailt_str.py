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
print(litteral_str == litteral_str_by_method)
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
print(len(msg) == 12)
msg2 = ""
print(len(msg2) == 1)
print(len(msg2) == 0)
# Quail-test:end


