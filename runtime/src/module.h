#ifndef MODULE_H_INCLUDED
#define MODULE_H_INCLUDED
#include "Python.h"

#if defined(_MSC_VER)
    //  Microsoft
    #define EXPORT __declspec(dllexport)
    #define IMPORT __declspec(dllimport)
#elif defined(__GNUC__)
    //  GCC
    #define EXPORT __attribute__((visibility("default")))
    #define IMPORT
#else
    //  do nothing and hope for the best?
    #define EXPORT
    #define IMPORT
    #pragma warning Unknown dynamic link import/export semantics.
#endif


EXPORT PyObject* flyable_import_name(PyObject *name, PyObject *fromlist, PyObject *level);


#endif // MODULE_H_INCLUDED
