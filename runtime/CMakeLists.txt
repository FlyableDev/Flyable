cmake_minimum_required(VERSION 3.13.4)
project(CodeGen)

find_package(PythonLibs REQUIRED)

add_library(
    runtime STATIC src/flyable.h src/module.h src/flyable.c 
src/module.c)


include_directories(${PYTHON_INCLUDE_DIRS})
target_link_libraries(runtime ${PYTHON_LIBRARIES})
