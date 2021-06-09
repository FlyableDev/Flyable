#include "flyable_object.h"

PyObject* __flyable__generate__class(char* name,char** names,void** funcs,int size)
{
    /*PyType_Spec* type = (PyType_Spec*) calloc(sizeof(PyType_Spec),1);
    type->name = name;
    type->basicsize = sizeof(XxoObject);
    type->itemsize = 1;
    type->flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC;

    PyMethodDef* methods = malloc(sizeof(PyMethodDef) * (size + 1));
    for(FlyInt i = 0;i < size;i++)
    {
        methods[i].ml_doc = "";
        methods[i].ml_flags = METH_METHOD | METH_FASTCALL | METH_KEYWORDS;
        methods[i].ml_name = names[i];
        methods[i].ml_meth = (PyCFunction) funcs[i];
    }



    PyType_Slot* slots = malloc(sizeof(PyType_Slot) * 8);
    slots[0].slot = Py_tp_doc;slots[0].pfunc = (char*) Xxo_doc;
    slots[1].slot = Py_tp_traverse;slots[1].pfunc = (char*) Xxo_traverse;
    slots[2].slot = Py_tp_finalize;slots[2].pfunc = (char*) Xxo_finalize;
    slots[3].slot = Py_tp_dealloc;slots[3].pfunc = (char*) Xxo_dealloc;
    slots[4].slot = Py_tp_getattro;slots[4].pfunc = (char*) Xxo_getattro;
    slots[5].slot = Py_tp_setattro;slots[5].pfunc = (char*) Xxo_setattro;
    slots[6].slot = Py_tp_methods;slots[6].pfunc = (char*) methods;
    slots[7].slot = NULL;slots[7].pfunc = NULL;

    type->slots = slots;


    methods[size].ml_doc = NULL;
    methods[size].ml_flags = NULL;
    methods[size].ml_meth = NULL;
    methods[size].ml_name = NULL;

     return PyType_FromSpec(type);*/
}
