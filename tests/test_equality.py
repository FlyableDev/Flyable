

def test_int_equality(compiled_value):
    are_values_equal = 15 == 15
    assert are_values_equal == compiled_value


def test_float_equality(compiled_value):
    are_values_equal = 15.12 == 15.12
    assert are_values_equal == compiled_value


def test_bool_equality(compiled_value):
    are_values_equal = False == False
    assert are_values_equal == compiled_value


def test_triple_equality(compiled_value):
    assert True == True == compiled_value


def test_zero_and_one_bool_comparison_with_is(compiled_value):
    int_to_bool_equality = 0 is False
    assert int_to_bool_equality == compiled_value


def test_zero_and_one_bool_comparison_with_equal(compiled_value):
    int_to_bool_equality = 1 == True
    assert int_to_bool_equality == compiled_value

