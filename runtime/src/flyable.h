#ifndef FLYABLE_H_INCLUDED
#define FLYABLE_H_INCLUDED
#include <Python.h>
#include <frameobject.h>
#include <pytypedefs.h>


void flyable_init();

PyObject* flyable_evalFrame(PyThreadState* ts, PyFrameObject* f, int throwflag);

//Represents the implementation of a flyable object
typedef struct FlyableImpl{
    PyTypeObject type;
    char* name;
    void* tp_call;
    void* vec_call;
}FlyableImpl;


void flyable_add_impl(char* name, void* tp, void* vec);

int flyable_set_implementation(PyObject* object);

void flyable_debug_print_int64(long long value);

void flyable_debug_print_cstr(char* debug);

void flyable_debug_print_ptr(char* ptr);

#endif // FLYABLE_H_INCLUDED
