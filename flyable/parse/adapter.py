import flyable.data.lang_func_impl as lang_func_impl


def adapt_call(func_name, call_type, args, comp_data, parser, codegen):
    """
    Handle the logic to make the function call possible.
    If it's a Flyable optimized object, it will specialise a function.
    Also handle Python object but doesn't do anything with it at the moment.
    """
    if call_type.is_obj():
        _class = comp_data.get_class(call_type.get_id())
        func = _class.get_func(func_name)
        if func is not None:
            return adapt_func(func, args, comp_data, parser)
    elif call_type.is_python_obj():
        return call_type

    # Any other type doesn't required the class
    return call_type


def adapt_func(func, args, comp_data, parser):
    """
    Specialise a function to the given arguments.
    Return an already specialise one if a matching one found.
    """
    if __validate(func, args):
        adapted_impl = func.find_impl_by_signature(args)
        if adapted_impl is not None:
            if not adapted_impl.get_parse_status() == lang_func_impl.LangFuncImpl.ParseStatus.ENDED:
                parser.parse_func(func)
        else:  # Need to create a new implementation
            comp_data.set_changed(True)  # A new implementation is a change to take in account
            adapted_impl = lang_func_impl.LangFuncImpl()
            for i, e in enumerate(args):
                adapted_impl.add_arg(args[i])
            func.add_impl(adapted_impl)
            parser.get_code_gen().gen_func(adapted_impl, parser.get_data())
            parser.parse_impl(adapted_impl)

        return adapted_impl

    return None


def __validate(func, args):
    """
    Make sure the function args count is compatible
    """
    min_args = func.get_min_args()
    max_args = func.get_max_args()
    if len(args) >= min_args and (len(args) <= max_args or max_args == -1):
        return True
    return False
