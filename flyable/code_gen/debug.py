import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen


def debug_call_addr_minus(visitor, v1, v2):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    func_name = "flyable_debug_addr_minus"
    func_call = code_gen.get_or_create_func(func_name, code_type.get_void(), [code_type.get_int8_ptr()] * 2,
                                            gen.Linkage.EXTERNAL)

    v1 = builder.ptr_cast(v1, code_type.get_int8_ptr())
    v2 = builder.ptr_cast(v2, code_type.get_int8_ptr())
    builder.call(func_call, [v1, v2])


def debug_support_vec(visitor, callable):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    func_name = "flyable_debug_support_vec"
    func_call = code_gen.get_or_create_func(func_name, code_type.get_void(), [code_type.get_int8_ptr()],
                                            gen.Linkage.EXTERNAL)

    callable = builder.ptr_cast(callable, code_type.get_int8_ptr())
    builder.call(func_call, [callable])


def flyable_debug_show_vec(visitor, callable, ptr):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    func_name = "flyable_debug_show_vec"
    func_call = code_gen.get_or_create_func(func_name, code_type.get_void(), [code_type.get_int8_ptr()] * 2,
                                            gen.Linkage.EXTERNAL)

    callable = builder.ptr_cast(callable, code_type.get_int8_ptr())
    ptr = callable = builder.ptr_cast(callable, code_type.get_int8_ptr())
    builder.call(func_call, [callable, ptr])


def flyable_debug_print_int64(visitor, value):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    func_name = "flyable_debug_print_int64"
    func_call = code_gen.get_or_create_func(func_name, code_type.get_void(), [code_type.get_int64()],
                                            gen.Linkage.EXTERNAL)
    builder.call(func_call, [value])

def flyable_debug_print_ptr(visitor, value):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    func_name = "flyable_debug_print_ptr"
    func_call = code_gen.get_or_create_func(func_name, code_type.get_void(), [code_type.get_int8_ptr()],
                                            gen.Linkage.EXTERNAL)
    value = builder.ptr_cast(value, code_type.get_int8_ptr())
    builder.call(func_call, [value])
