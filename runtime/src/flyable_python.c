#include "flyable_python.h"
#include "object/flyable_object.h"



int __flyable__print(PyObject* obj)
{
    PyObject* objectsRepresentation = PyObject_Repr(obj);
    const char* s = PyUnicode_AsUTF8AndSize(objectsRepresentation,NULL);
    printf(s);
    printf("\n");
    return 0;
}
