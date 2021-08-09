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
