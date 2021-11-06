#include "debug.h"


void flyable_debug_addr_minus(void* addr1,void* addr2)
{
    void* result = addr2 - addr1;

    PyTypeObject* obj = addr1;
    PyTupleObject* test;
    test->ob_item[0] = NULL;

    printf("%d  \n",(int) (addr2 - addr1));

}

void flyable_debug_support_vec(PyObject* obj)
{

    vectorcallfunc func = PyVectorcall_Function(obj);
    if(func != NULL)
        printf("DOES SUPPORT VEC CALL\n");
    else
        printf("DOESNT SUPPORT VECL CALL\n");
}

void flyable_debug_show_vec(PyObject* obj,PyObject* call)
{
    size_t offset = Py_TYPE(obj)->tp_vectorcall_offset;

    printf("%p\n",(char*) obj + offset);
}

void flyable_debug_print_int64(long long value)
{

    printf("%lld\n", value);
}

void flyable_debug_print_ptr(void* ptr)
{
    printf("%p\n",ptr);
}

void debug_is_tuple(PyObject* tuple)
{
    printf("%p      %p\n",tuple,&PyTuple_Type);
}
