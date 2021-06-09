#ifndef FLYABLE_OBJECT_H_INCLUDED
#define FLYABLE_OBJECT_H_INCLUDED

#define PY_SSIZE_T_CLEAN
#include <Python.h>


// Module state

typedef struct {
    PyObject *Xxo_Type;    // Xxo class
    PyObject *Error_Type;       // Error class
} xx_state;


/* Xxo objects */

// Instance state
typedef struct {
    PyObject_HEAD
    PyObject            *x_attr;        /* Attributes dictionary */
} XxoObject;

static XxoObject * newXxoObject(PyObject *module)
{
    xx_state *state = PyModule_GetState(module);
    if (state == NULL) {
        return NULL;
    }

    XxoObject *self;
    self = PyObject_GC_New(XxoObject, (PyTypeObject*)state->Xxo_Type);

    if (self == NULL)
    {
        return NULL;
    }

    self->x_attr = NULL;

    return self;
}

static int Xxo_traverse(XxoObject *self, visitproc visit, void *arg)
{
    // Visit the type
    Py_VISIT(Py_TYPE(self));

    // Visit the attribute dict
    Py_VISIT(self->x_attr);
    return 0;
}

static void Xxo_finalize(XxoObject *self)
{
    Py_CLEAR(self->x_attr);
}

static PyObject* Xxo_getattro(XxoObject *self, PyObject *name)
{
    if (self->x_attr != NULL) {
        PyObject *v = PyDict_GetItemWithError(self->x_attr, name);
        if (v != NULL) {
            Py_INCREF(v);
            return v;
        }
        else if (PyErr_Occurred()) {
            return NULL;
        }
    }
    return PyObject_GenericGetAttr((PyObject *)self, name);
}

static int Xxo_setattro(XxoObject *self, PyObject *name, PyObject *v)
{
    if (self->x_attr == NULL) {
        // prepare the attribute dict
        self->x_attr = PyDict_New();
        if (self->x_attr == NULL) {
            return -1;
        }
    }
    if (v == NULL) {
        // delete an attribute
        int rv = PyDict_DelItem(self->x_attr, name);
        if (rv < 0 && PyErr_ExceptionMatches(PyExc_KeyError)) {
            PyErr_SetString(PyExc_AttributeError,
                "delete non-existing Xxo attribute");
            return -1;
        }
        return rv;
    }
    else {
        // set an attribute
        return PyDict_SetItem(self->x_attr, name, v);
    }
}

static PyObject* Xxo_demo(XxoObject *self, PyTypeObject *defining_class,PyObject **args, Py_ssize_t nargs, PyObject *kwnames)
{
    if (kwnames != NULL && PyObject_Length(kwnames)) {
        PyErr_SetString(PyExc_TypeError, "demo() takes no keyword arguments");
        return NULL;
    }
    if (nargs != 1) {
        PyErr_SetString(PyExc_TypeError, "demo() takes exactly 1 argument");
        return NULL;
    }

    PyObject *o = args[0];

    /* Test if the argument is "str" */
    if (PyUnicode_Check(o)) {
        Py_INCREF(o);
        return o;
    }

    /* test if the argument is of the Xxo class */
    if (PyObject_TypeCheck(o, defining_class)) {
        Py_INCREF(o);
        return o;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef Xxo_methods[] = {
    {"demo",            (PyCFunction)(void(*)(void))Xxo_demo,
     METH_METHOD | METH_FASTCALL | METH_KEYWORDS, PyDoc_STR("demo(o) -> o")},
    {NULL,              NULL}           /* sentinel */
};

PyDoc_STRVAR(Xxo_doc,"A class that explicitly stores attributes in an internal dict");


static void Xxo_dealloc(XxoObject *self)
{
    Xxo_finalize(self);
    PyTypeObject *tp = Py_TYPE(self);
    freefunc free = PyType_GetSlot(tp, Py_tp_free);
    PyMem_FREE(self);
    Py_DECREF(tp);
}

static PyType_Slot Xxo_Type_slots[] = {
    {Py_tp_doc, (char *)Xxo_doc},
    {Py_tp_traverse, Xxo_traverse},
    {Py_tp_finalize, Xxo_finalize},
    {Py_tp_dealloc, Xxo_dealloc},
    {Py_tp_getattro, Xxo_getattro},
    {Py_tp_setattro, Xxo_setattro},
    {Py_tp_methods, Xxo_methods},
    {0, 0},  /* sentinel */
};

static PyType_Spec Xxo_Type_spec = {
    .name = "xxlimited.Xxo",
    .basicsize = sizeof(XxoObject),
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
    .slots = Xxo_Type_slots,
};


/* Function of two integers returning integer (with C "long int" arithmetic) */

PyDoc_STRVAR(xx_foo_doc,
"foo(i,j)\n\
\n\
Return the sum of i and j.");

static PyObject *
xx_foo(PyObject *module, PyObject *args)
{
    long i, j;
    long res;
    if (!PyArg_ParseTuple(args, "ll:foo", &i, &j))
        return NULL;
    res = i+j; /* XXX Do something here */
    return PyLong_FromLong(res);
}


/* Function of no arguments returning new Xxo object */

static PyObject *
xx_new(PyObject *module, PyObject *Py_UNUSED(unused))
{
    XxoObject *rv;

    rv = newXxoObject(module);
    if (rv == NULL)
        return NULL;
    return (PyObject *)rv;
}

/* List of functions defined in the module */

static PyMethodDef xx_methods[] = {
    {"foo",             xx_foo,         METH_VARARGS,xx_foo_doc},
    {"new",             xx_new,         METH_NOARGS,PyDoc_STR("new() -> new Xx object")},
    {NULL,              NULL}           /* sentinel */
};

#endif // FLYABLE_OBJECT_H_INCLUDED
