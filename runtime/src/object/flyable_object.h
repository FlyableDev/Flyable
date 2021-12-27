#ifndef FLYABLE_OBJECT_H_INCLUDED
#define FLYABLE_OBJECT_H_INCLUDED

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "map.h"

#define FLYABLE_ATTR_TYPE_INT 1
#define FLYABLE_ATTR_TYPE_DEC 2
#define FLYABLE_ATTR_TYPE_OBJ 3
#define FLYABLE_ATTR_TYPE_METHOD 4

typedef struct
{
    PyTypeObject type;
    hashmap* attrMap;
}FlyableClass;

typedef struct
{
    int type;
    int index;
    void* ptr;
}FlyableClassAttr;

FlyableClass* flyable_class_alloc();

void flyable_class_set_attr_index(FlyableClass* flyClass,char* attr,int index,int type);

void flyable_class_set_method(FlyableClass* flyClass,char* attr,void* tp,void* vec);

PyObject* flyable_class_get_attr(PyObject* obj,char* str);

PyObject* flyable_class_get_attro(PyObject* obj,PyObject* str);

int flyable_class_set_attr(PyObject* obj,char* str, PyObject* objSet);

int flyable_class_set_attro(PyObject* obj,PyObject* str, PyObject* objSet);

void flyable_class_dealloc(PyObject* obj);


#endif // FLYABLE_OBJECT_H_INCLUDED
