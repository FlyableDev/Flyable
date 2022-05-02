#ifndef GENERATOR_H
#define GENERATOR_H
#include <Python.h>
#include "internal/pycore_frame.h"

extern PyObject* _PyEval_EvalFrameDefault(PyThreadState* ts, _PyInterpreterFrame* f, int throwflag);
extern _PyInterpreterFrame * _PyEval_GetFrame();
extern PyObject* _Py_MakeCoro(PyFunctionObject *func);
extern void _Py_LeaveRecursiveCall();
extern PyObject* _PyErr_Occurred(PyThreadState *tstate);
extern void _PyInterpreterState_SetEvalFrameFunc();

PyObject* flyable_handle_return_generator_bytecode();

#endif // GENERATOR_H