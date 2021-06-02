![alt text](https://www.flyabledev.com/images/logo_flyable.svg)
# Flyable - A python compiler for highly performant code

https://www.flyable.dev

Flyable is a python compiler that generates efficient native code. It uses different technics and aggressive optimizations to make sure your code runs the way you want the fastest way possible. It also relies on CPython to make sure that all your favorite libraries are still available and fully functional.

Flyable is under the GNU Affero General Public License v3.0 .


# How does it work ?
Flyable does multiple things to generate efficient code but most of the perfomance gain comes from the following:
- Native execution of the code
- Static function dispatch (enabling direct call and efficient inlining)
- Type tracking (When possible)
- Function specialization depending on the signature but also on the usage

# Supported platforms
Flyable only generated code for Windows 64 bits x86 for now. It will quickly be extented to Linux and Mac.

# How to use it ?
For now, Flyable is only available as a module that read a python file and outputs an object file. To run the output, the object file must be link with any  the python39.lib file available in your Python installation. To run a Flyable made executable, it is required to have an active CPython installation setup on the machine.

Flyable is still in a early stage. We do not recommend full scale usage at the moment.

# Plan
Most of our current efforts are put on stabilising the compiler to support most of python syntax and optimize the most common use cases of python.

# Contributions
We do accept and review external contributions. Feel free to open an issue. Contact us at contact@flyable.dev if you have any other concerns.
