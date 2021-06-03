import flyable.data.lang_func as lang_func
import flyable.data.lang_func_impl as lang_func_impl
import flyable.data.argument as argument


def adapt_func(func, args, comp_data, parser):
    if __validate(func, args):
        adapted_impl = func.find_impl_by_signature(args)
        if adapted_impl is not None:
            if adapted_impl.is_parse_started() == False:
                parser.parse_func(comp_data, func)
        else:  # Need to create a new implementation
            adapted_impl = lang_func_impl.LangFuncImpl()
            for i, e in enumerate(args):
                adapted_impl.add_arg(args[i])
            func.add_impl(adapted_impl)
            parser.parse_impl(comp_data, adapted_impl)

        return adapted_impl

    return None


def __validate(func, args):
    # Make sure the fonction args count is compatible
    min_args = func.get_min_args()
    max_args = func.get_max_args()
    if len(args) >= min_args and (len(args) <= max_args or max_args == -1):
        return True
    return False
