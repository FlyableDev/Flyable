#include "exception.h"


void flyable_raise_index_error()
{
    PyErr_SetString(PyExc_IndexError, "list index out of range");
}

void flyable_raise_callable_error()
{
    PyErr_SetString(PyExc_TypeError, "object is not callable");
}
