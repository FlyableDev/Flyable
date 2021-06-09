

#ifdef __linux__
    #define _FILE_OFFSET_BITS 64
    #include <sys/types.h>
#endif // __linux__

#ifdef __EMSCRIPTEN__
    #include <emscripten.h>
#endif // __EMSCRIPTEN


//include all files/
#include "math.h"
#include "platform.h"
#include "flyable_python.h"





