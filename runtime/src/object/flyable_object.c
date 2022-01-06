#include "flyable_object.h"

FlyableClass* flyable_class_alloc()
{
    FlyableClass* result = (FlyableClass*) calloc(sizeof(FlyableClass),1);
    result->attrMap = hashmap_create();
    result->type.ob_base.ob_base.ob_refcnt = 2; //avoid the object destruction
    result->type.tp_getattr = &flyable_class_get_attr;
    result->type.tp_getattro = &flyable_class_get_attro;
    result->type.tp_setattr = &flyable_class_set_attr;
    result->type.tp_setattro = &flyable_class_set_attro;
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

void flyable_class_set_method(FlyableClass* flyClass,char* attr,void* tp,void* vec)
{
    //for every method we need a class the describes it
    PyTypeObject* object = (PyTypeObject*) calloc(sizeof(PyTypeObject),1);
    object->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_VECTORCALL;
    object->tp_vectorcall_offset = sizeof(PyMethodObject) - sizeof(void*); //the ptr is at the end of the struct
    object->ob_base.ob_base.ob_refcnt = 1;
    object->tp_vectorcall = vec;
    object->tp_call = tp;

    FlyableClassAttr* newAttr = (FlyableClassAttr*) malloc(sizeof(FlyableClassAttr));
    newAttr->type = FLYABLE_ATTR_TYPE_METHOD;
    newAttr->ptr = object;
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
            PyObject** result =  (PyObject**) obj + (attr->index / sizeof(PyObject*));
            int attrType = attr->type;

            if(attrType == FLYABLE_ATTR_TYPE_INT)
            {
                return PyLong_FromLongLong(*((long long*) result));
            }
            else if(attrType == FLYABLE_ATTR_TYPE_DEC)
            {
                return PyFloat_FromDouble((*(double*) result));
            }
            else if(attrType == FLYABLE_ATTR_TYPE_METHOD)
            {
                PyTypeObject* object = (PyTypeObject*) attr->ptr;
                PyMethodObject* method = (PyMethodObject*) malloc(sizeof(PyMethodObject));
                method->im_self = obj;
                method->im_func = flyClass;
                method->im_weakreflist = NULL;
                method->vectorcall = object->tp_vectorcall;
                method->ob_base.ob_refcnt = 2;
                method->ob_base.ob_type = &PyMethod_Type;
                ++PyMethod_Type.ob_base.ob_base.ob_refcnt;
                ++flyClass->type.ob_base.ob_base.ob_refcnt;
                ++obj->ob_refcnt;
                return method;
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

PyObject* flyable_class_get_attro(PyObject* obj,PyObject* pyStr)
{
    if(PyUnicode_CheckExact(pyStr))
    {
        PyUnicodeObject* unicodeObj = (PyUnicodeObject*) pyStr;
        char* str = (char*) PyUnicode_DATA(pyStr);
        size_t size = unicodeObj->_base._base.length;


        FlyableClass* flyClass = (FlyableClass*) obj->ob_type;
        FlyableClassAttr* attr;
        if(hashmap_get(flyClass->attrMap,str,size,&attr))
        {
            if(attr != NULL)
            {
                PyObject** result =  (PyObject**) obj + (attr->index / sizeof(PyObject*));
                int attrType = attr->type;

                if(attrType == FLYABLE_ATTR_TYPE_INT)
                {
                    return PyLong_FromLongLong(*((long long*) result));
                }
                else if(attrType == FLYABLE_ATTR_TYPE_DEC)
                {
                    return PyFloat_FromDouble((*(double*) result));
                }
                else if(attrType == FLYABLE_ATTR_TYPE_METHOD)
                {
                    PyTypeObject* object = (PyTypeObject*) attr->ptr;
                    PyMethodObject* method = (PyMethodObject*) malloc(sizeof(PyMethodObject));
                    method->im_self = obj;
                    method->im_func = flyClass;
                    method->im_weakreflist = NULL;
                    method->vectorcall = object->tp_vectorcall;
                    method->ob_base.ob_refcnt = 2;
                    method->ob_base.ob_type = &PyMethod_Type;
                    ++PyMethod_Type.ob_base.ob_base.ob_refcnt;
                    ++flyClass->type.ob_base.ob_base.ob_refcnt;
                    ++obj->ob_refcnt;
                    return method;
                }
                else
                {
                    const PyObject* loadResult = *result;
                    Py_IncRef(loadResult);
                    return loadResult;
                }
            }
        }


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
            PyObject** result =  (PyObject**) obj + (attr->index / sizeof(PyObject*));
            *result = objSet;
            ++objSet->ob_refcnt;
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
