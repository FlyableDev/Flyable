#ifndef DEBUG_H_INCLUDED
#define DEBUG_H_INCLUDED
#include <Python.h>

void flyable_debug_addr_minus(void* addr1,void* addr2);

void flyable_debug_support_vec(PyObject* obj);

void flyable_debug_show_vec(PyObject* obj,PyObject* call);

void flyable_debug_print_int64(long long value);

void flyable_debug_print_ptr(void* ptr);

void debug_is_tuple(PyObject* tuple);

#endif // DEBUG_H_INCLUDED
