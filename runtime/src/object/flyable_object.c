#include "flyable_object.h"

FlyableClass* flyable_class_alloc()
{
    FlyableClass* result = (FlyableClass*) calloc(sizeof(FlyableClass),1);
    result->attrMap = hashmap_create();
    result->type.ob_base.ob_base.ob_refcnt = 2; //avoid the object destruction
    result->type.tp_getattr = &flyable_class_get_attr;
    result->type.tp_getattro = &flyable_class_get_attro;
    result->type.tp_setattr = &flyable_class_get_attr;
    result->type.tp_setattro = &flyable_class_get_attro;
    result->type.tp_dealloc = &flyable_class_dealloc;
    return result;
}

void flyable_class_set_attr_index(FlyableClass* flyClass,char* attr,int type,int index)
{
    FlyableClassAttr* newAttr = (FlyableClassAttr*) malloc(sizeof(FlyableClassAttr));
    newAttr->type = type;
    newAttr->index = index;
    hashmap_set(flyClass->attrMap,attr,strlen(attr),newAttr);
}

PyObject* flyable_class_get_attr(PyObject* obj,char* str)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;

    FlyableClassAttr* attr;
    if(hashmap_get(flyClass->attrMap,str,strlen(str),&attr))
    {
        if(attr != NULL)
        {
            PyObject** result =  (PyObject**) obj + attr->index;
            int attrType = attr->type;

            if(attrType == FLYABLE_ATTR_TYPE_INT)
            {
                return PyLong_FromLongLong(*((long long*) result));
            }
            else if(attrType == FLYABLE_ATTR_TYPE_DEC)
            {
                return PyFloat_FromDouble((*(double*) result));
            }
            else
            {
                const PyObject* loadResult = *result;
                Py_IncRef(loadResult);
                return loadResult;
            }
        }
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* flyable_class_get_attro(PyObject* obj,PyObject* str)
{
    if(PyUnicode_CheckExact(str))
    {
        size_t strSize;
        char* txt = PyUnicode_AsUTF8AndSize(str,&strSize);
        return flyable_class_get_attr(obj,txt);
    }

    Py_INCREF(Py_None);
    return Py_None;
}

int flyable_class_set_attr(PyObject* obj,char* str, PyObject* objSet)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
    FlyableClassAttr* attr;
    if(hashmap_get(flyClass->attrMap,str,strlen(str),&attr))
    {
        if(attr != NULL)
        {
            PyObject** result =  (PyObject**) obj + attr->index;
            *result = objSet;
            return 1;
        }
    }

    return 0;
}

int flyable_class_set_attro(PyObject* obj,PyObject* str, PyObject* objSet)
{
    if(PyUnicode_CheckExact(str))
    {
        FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
        size_t strSize;
        char* txt = PyUnicode_AsUTF8AndSize(str,&strSize);
        return flyable_class_set_attr(obj,txt,objSet);
    }

    return 0;
}

void flyable_class_dealloc(PyObject* obj)
{

}
