#ifndef PLATFORM_H_INCLUDED
#define PLATFORM_H_INCLUDED

int __flyable_runtime__get__platform()
{
    #ifdef __WIN32
        return 1;
    #endif // __WIN32

    #ifdef __EMSCRIPTEN__
        return 2;
    #endif // __WIN32

    #ifdef __linux__
        return 3;
    #endif // __linux__

    #ifdef __APPLE__
        #include "TargetConditionals.h"
        #ifdef TARGET_OS_IPHONE
             return 6;
        #elif TARGET_IPHONE_SIMULATOR
            return 6;
        #elif TARGET_OS_MAC
            return 4;
        #else
            return 0;
        #endif
    #endif

    return 0;
}

#endif // PLATFORM_H_INCLUDED
