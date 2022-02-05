"""Module where str body tests are created"""

# Flytest:new
"""
Name: empty_str_creation
Flyable-version: v0.1a1
Description: Test that the result of "" equals the result of calling str()
"""
# Flytest:start
litteral_str = ""
litteral_str_by_method = str()
print("YOOOOOOOOOOOOOOOOOOOOOOLOOOOOOOOOOOOOOO")
#print(litteral_str == litteral_str_by_method)
# Flytest:end


# Flytest:new
"""
Name: len_str
Flyable-version: v0.1a1
Description: Test that the len function works properly on strings
"""
# Flytest:start
msg = "hello world!"
len_msg = len(msg)
print(len(msg) == 12)
# Flytest:end
