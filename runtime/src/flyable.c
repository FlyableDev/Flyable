#include "flyable.h"
#include "internal/pycore_frame.h"

extern PyObject* _PyEval_EvalFrameDefault(PyThreadState* ts, PyFrameObject* f, int throwflag);

FlyableImpl* FlyableImpls = NULL;
int FlyableImplsCount = 0;

static PyInterpreterState* inter()
{
    return PyInterpreterState_Main();
}

void flyable_init()
{
    _PyInterpreterState_SetEvalFrameFunc(inter(), flyable_evalFrame);
}

PyObject* flyable_evalFrame(PyThreadState* ts, PyFrameObject* f, int throwflag)
{
    //The call to flyable eval frame is done because the pointers to the call are not switch yet
    _PyInterpreterFrame* ff = (_PyInterpreterFrame*) f;

    if(ff != NULL && ff->f_func != NULL)
    {
        if(flyable_set_implementation(ff->f_func)) // The pointer got changed
        {
        }
    }

    //When the pointer is switch, we do the call normally
    return _PyEval_EvalFrameDefault(ts,f, throwflag);
}


void flyable_add_impl(char* name, void* tp, void* vec)
{
    if (FlyableImplsCount == 0)
    {
        FlyableImpls = (FlyableImpl*) malloc(sizeof(FlyableImpl));
        FlyableImplsCount = 1;
    }
    else
    {
        ++FlyableImplsCount;
        FlyableImpls = (FlyableImpl*) realloc(FlyableImpls, sizeof(FlyableImpl) * FlyableImplsCount);
    }

    FlyableImpl* newImpl = &FlyableImpls[FlyableImplsCount - 1];
    newImpl->name = name;
    newImpl->tp_call = tp;
    newImpl->vec_call = vec;
}

//Get an object and try to match it to replace the given pointers
int flyable_set_implementation(PyObject* object)
{
    for (int i = 0; i < FlyableImplsCount; ++i)
    {
        FlyableImpl* currentImpl = &FlyableImpls[i];
        PyTypeObject* implType = &FlyableImpls[i].type;

        if (PyMethod_Check(object))
        {
            PyMethodObject* method = (PyMethodObject*)object;
            object = method->im_func;
        }

        if (PyFunction_Check(object))
        {
            PyFunctionObject* funcObj = (PyFunctionObject*)object;
            PyTypeObject* callType = object->ob_type;


            if (PyUnicode_CompareWithASCIIString(funcObj->func_qualname, currentImpl->name) == 0)
            {
                memcpy((void*)implType, (void*)&PyFunction_Type, sizeof(PyFunction_Type));
                implType->tp_name = "Flyable function";

                //Change the function type so it refers to a flyable type
                Py_SET_TYPE(funcObj, implType);
                Py_INCREF(implType);

                //Change the type funcs so it refers to flyable calls
                implType->tp_vectorcall = currentImpl->vec_call;
                implType->tp_call = currentImpl->tp_call;

                //Make sure the types indicates that it supportes vec call
                implType->tp_flags = implType->tp_flags & _Py_TPFLAGS_HAVE_VECTORCALL;

                //Set the type vector offset
                currentImpl->type.tp_vectorcall_offset = (char*) &funcObj->vectorcall -  (char*) funcObj;

                //Set the vector call using the offset
                char** offset = (char**)funcObj;
                offset += callType->tp_vectorcall_offset;
                *offset = (char*) currentImpl->vec_call;
                funcObj->vectorcall = currentImpl->vec_call;
                return 1;
            }
        }
    }

    return 0;
}

void flyable_debug_print_int64(long long value)
{
    printf("%d\n",value);
}

void flyable_debug_print_cstr(char* debug)
{
    printf(debug);
}

void flyable_debug_print_ptr(char* ptr)
{
    printf("%p\n", ptr);
}

