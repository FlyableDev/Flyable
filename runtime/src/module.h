#ifndef MODULE_H_INCLUDED
#define MODULE_H_INCLUDED
#include "Python.h"


__declspec(dllexport)  PyObject* flyable_import_name(PyObject *name, PyObject *fromlist, PyObject *level);


#endif // MODULE_H_INCLUDED
