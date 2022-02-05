class FlyUnitTest:
    def compile_code(self, code):
        pass

    def assert_ref_count(self, var, number):
        pass

    def assert_func_impl(self, func, *function_impl: tuple[list[type], type]):
        pass


# ///////////////////////////////////////////////////////


class FlyStrTests(FlyUnitTest):
    def __init__(self):
        ...

    def fly_test_str_equality(self):
        a = "abc"
        b = "abc"
        print(a)
        print(a == b)

    def fly_test_list_creation(self):
        """
        Name:
        Decription:
        """
        self.assert_func_impl("func1", ([str], str), ([int], int))

        # Fly::start

        def func1(param):
            return param + param

        func1(12)

        # Fly::pause
        self.assert_func_impl("func1", ([int], int))
        # Fly::resume

        func1("aa")

        # Fly::end
