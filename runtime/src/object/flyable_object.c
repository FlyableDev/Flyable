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
            PyObject* result =  (PyObject*) obj + attr->index;
            int attrType = attr->type;
            if(attrType == FLYABLE_ATTR_TYPE_INT)
            {
                return PyLong_FromLongLong((*(long long*) result));
            }
            else if(attrType == FLYABLE_ATTR_TYPE_DEC)
            {
                return PyFloat_FromDouble((*(double*) result));
            }
            else
            {
                Py_IncRef(result);
                return result;
            }
        }
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* flyable_class_get_attro(PyObject* obj,PyObject* str)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
    if(PyUnicode_Check(obj))
    {
        char* str = PyUnicode_DATA(obj);
        Py_ssize_t strSize = PyUnicode_GET_LENGTH(obj);
        long long outValue;
        if(hashmap_get(flyClass->attrMap,str,strSize,&outValue))
        {
            PyObject* result =  (PyObject*) obj + outValue;
            Py_IncRef(result);
            return result;
        }
    }

    Py_INCREF(Py_None);
    return Py_None;
}

int flyable_class_set_attr(PyObject* obj,char* str, PyObject* objSet)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
}

int flyable_class_set_attro(PyObject* obj,PyObject* str, PyObject* objSet)
{
    FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
}

void flyable_class_dealloc(PyObject* obj)
{

}
