#ifndef FLYABLE_OBJECT_H_INCLUDED
#define FLYABLE_OBJECT_H_INCLUDED

#define PY_SSIZE_T_CLEAN
#include <Python.h>

typedef struct
{
    PyTypeObject type;
    //hashmap addrMap;
} FlyableClass;



PyObject* flyable_class_get_attr(PyObject* obj,char* str);

PyObject* flyable_class_get_attro(PyObject* obj,PyObject* str);

int flyable_class_set_attr(PyObject* obj,char* str, PyObject* objSet);

int flyable_class_set_attro(PyObject* obj,PyObject* str, PyObject* objSet);


#endif // FLYABLE_OBJECT_H_INCLUDED
