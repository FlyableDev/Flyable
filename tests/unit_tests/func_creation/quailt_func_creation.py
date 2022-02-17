"""Module func_creation"""

# Quail-test:new compile
"""
Name: func_creation
Flyable-version: v0.1a1
Description: test to see if flyable can create functions
"""
# Quail-test:start
def gt2(param: int, param2):
    return param > 2

def abc(param: int):
    return param > 2


abc(2)
gt2([1, 2], 12)
# Quail-test:end
