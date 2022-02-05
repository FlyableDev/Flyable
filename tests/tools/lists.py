from typing import Callable


def flytest(func: Callable):
    pass


def fly_assert_func_impl(func: str, args, return_value):
    pass


@flytest
def fly_test_list_creation():
    """
    Name:
    Decription:
    """
    fly_assert_func_impl("func1", ([str], str), ([int], int))

    """Fly::start"""

    def func1(param):
        return param + param

    func1(12)
    func1("aa")

    """Fly::end"""


fly_test_list_creation()
