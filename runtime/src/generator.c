#include "generator.h"

PyObject* flyable_handle_return_generator_bytecode()
{
    PyThreadState* tstate = PyThreadState_Get();
    _PyCFrame* cframe = tstate->cframe;
    _PyInterpreterFrame* frame = _PyEval_GetFrame();
    PyObject** stack_pointer = _PyFrame_GetStackPointer(frame);

    PyGenObject* gen = (PyGenObject *)_Py_MakeCoro(frame->f_func);
    _PyFrame_SetStackPointer(frame, stack_pointer);
    _PyInterpreterFrame *gen_frame = (_PyInterpreterFrame *)gen->gi_iframe;
    _PyFrame_Copy(frame, gen_frame);
    assert(frame->frame_obj == NULL);
    gen->gi_frame_state = FRAME_CREATED;
    gen_frame->owner = FRAME_OWNED_BY_GENERATOR;

    _Py_LeaveRecursiveCall(tstate);
    if (!frame->is_entry) {
        _PyInterpreterFrame *prev = frame->previous;
        _PyThreadState_PopFrame(tstate, frame);
        frame = cframe->current_frame = prev;
        _PyFrame_StackPush(frame, (PyObject *)gen);

        // resume frame
        PyCodeObject *co = frame->f_code;
        PyObject* names = co->co_names;
        PyObject* consts = co->co_consts;
        _Py_CODEUNIT* first_instr = _PyCode_CODE(co);
        // TODO: update on next release this has been change in main branch to:
        // _Py_CODEUNIT* next_instr = frame->prev_instr + 1;
        _Py_CODEUNIT* next_instr = frame->f_lasti + 1;
        
        stack_pointer = _PyFrame_GetStackPointer(frame);
        /* Set stackdepth to -1.
            Update when returning or calling trace function.
            Having stackdepth <= 0 ensures that invalid
            values are not visible to the cycle GC.
            We choose -1 rather than 0 to assist debugging.
            */
        frame->stacktop = -1;

        /* Make sure that frame is in a valid state */
        frame->stacktop = 0;
        frame->f_locals = NULL;
        Py_INCREF(frame->f_func);
        Py_INCREF(frame->f_code);
        /* Restore previous cframe and return. */
        tstate->cframe = cframe->previous;
        tstate->cframe->use_tracing = cframe->use_tracing;
        assert(tstate->cframe->current_frame == frame->previous);
        assert(!_PyErr_Occurred(tstate));
        return (PyObject *)gen;
    }
}