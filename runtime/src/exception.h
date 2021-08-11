#ifndef EXCEPTION_H_INCLUDED
#define EXCEPTION_H_INCLUDED
#include <Python.h>

void flyable_raise_index_error();

void flyable_raise_callable_error();

void flyable_raise_assert_error(PyObject* obj);

#endif // EXCEPTION_H_INCLUDED
