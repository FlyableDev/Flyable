

def test_if_statement(compiled_value):
    my_val = ""
    if True:
        my_val = "The condition passed"
    assert my_val == compiled_value


def test_if_else_statement(compiled_value):
    my_val = 0
    if False:
        my_val = 1
    else:
        my_val = 2
    assert my_val == compiled_value


def test_if_elif_statement(compiled_value):
    my_val = 0
    if False:
        my_val = 1
    elif False:
        my_val = 2
    assert my_val == compiled_value


def test_if_elif_else_statement(compiled_value):
    if False:
        my_val = 1
    elif False:
        my_val = 2
    else:
        my_val = 3
    assert my_val == compiled_value
