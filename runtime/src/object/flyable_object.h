#ifndef FLYABLE_OBJECT_H_INCLUDED
#define FLYABLE_OBJECT_H_INCLUDED

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "map.h"

#define FLYABLE_ATTR_TYPE_INT 1
#define FLYABLE_ATTR_TYPE_DEC 2
#define FLYABLE_ATTR_TYPE_OBJ 3

typedef struct
{
    PyTypeObject type;
    hashmap* attrMap;
} FlyableClass;

FlyableClass* flyable_class_alloc();

void flyable_class_set_attr_index(FlyableClass* flyClass,char* attr,long long index);

PyObject* flyable_class_get_attr(PyObject* obj,char* str);

PyObject* flyable_class_get_attro(PyObject* obj,PyObject* str);

int flyable_class_set_attr(PyObject* obj,char* str, PyObject* objSet);

int flyable_class_set_attro(PyObject* obj,PyObject* str, PyObject* objSet);


#endif // FLYABLE_OBJECT_H_INCLUDED
