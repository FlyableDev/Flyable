cmake_minimum_required(VERSION 3.13.4)
project(CodeGen)

find_package(PythonLibs REQUIRED)

add_library(
    FlyableRuntime STATIC src/debug.h src/exception.h src/debug.c src/exception.c src/flyable_python.c src/flyable_python.h 
    src/list.c src/list.c src/list.h src/math.c src/math.h src/main.c src/object/flyable_object.c src/object/flyable_object.h 
    src/object/map.c src/object/map.h src/platform.h)


include_directories(${PYTHON_INCLUDE_DIRS})
target_link_libraries(FlyableRuntime ${PYTHON_LIBRARIES})
