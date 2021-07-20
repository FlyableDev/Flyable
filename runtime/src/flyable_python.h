#ifndef FLYABLE_PYTHON_H_INCLUDED
#define FLYABLE_PYTHON_H_INCLUDED

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <object.h>
#include <abstract.h>

typedef struct {
    PyObject_HEAD
    PyObject *car, *cdr;
} cons_cell;

static PyTypeObject cons_type;


int __flyable__print(PyObject* obj);


#endif // FLYABLE_PYTHON_H_INCLUDED
