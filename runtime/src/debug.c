#include "debug.h"


void flyable_debug_addr_minus(void* addr1,void* addr2)
{
    void* result = addr2 - addr1;

    PyTypeObject* obj = addr1;

    printf("%d  %d\n",(int) (addr2 - addr1), (int)(((void*) &obj->tp_getattro) - addr1));



    printf("%d\n",sizeof(obj->));
}
