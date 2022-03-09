"""Module func_creation"""

# Quail-test:new compile
"""
Name: func_creation
Flyable-version: v0.1a1
Description: test to see if flyable can create functions
"""
# Quail-test:start
def abc(param1: bool):
    return param1 > 2


def gt2(param: int, param2):
    return param > 2


# Quail-test:end


# Quail-test:new
"""
Name: variable
Flyable-version: v0.1a1
Description: test vars
"""
# Quail-test:start

b = ["123"]

# Quail-test:end
