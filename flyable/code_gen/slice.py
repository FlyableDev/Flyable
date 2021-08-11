import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen


def py_slice_new(visitor, start, stop, step):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    func = code_gen.get_or_create_func("PySlice_New", code_type.get_py_obj_ptr(code_gen),
                                       [code_type.get_py_obj_ptr(code_gen)] * 3, gen.Linkage.EXTERNAL)

    return builder.call(func, [start, stop, step])
