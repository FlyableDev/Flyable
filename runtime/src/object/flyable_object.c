#include "flyable_object.h"
#include "map.h"


PyObject* flyable_class_get_attr(PyObject* obj,char* str)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
}

PyObject* flyable_class_get_attro(PyObject* obj,PyObject* str)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
}

int flyable_class_set_attr(PyObject* obj,char* str, PyObject* objSet)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
}

int flyable_class_set_attro(PyObject* obj,PyObject* str, PyObject* objSet)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
}
