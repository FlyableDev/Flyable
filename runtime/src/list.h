#ifndef LIST_H_INCLUDED
#define LIST_H_INCLUDED
#include <Python.h>

int python_list_resize(PyListObject *self, Py_ssize_t newsize);

PyObject* flyable_get_tuple_type();


#endif // LIST_H_INCLUDED
