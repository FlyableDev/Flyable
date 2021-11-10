![alt text](https://www.flyabledev.com/images/logo_flyable.svg)
# Flyable - A python compiler for highly performant code

Flyable is a Python compiler that generates efficient native code. It uses different techniques and aggressive optimizations to make sure your code runs the way you want: the fastest way possible. It also relies on CPython to make sure that all your favorite libraries are still available and fully functional.

- [Website](https://www.flyable.dev)
- [Discord (new)] (https://discord.gg/tquHUe9Q89)
- [Documentation](https://flyabledev.github.io/FlyableDoc/#/)
- [Gitter](https://gitter.im/FlyableDev/community)

Flyable is licensed under the GNU Affero General Public License v3.0 .

# Build
Make sure that you have downloaded the GCC compiler and you have an active CPython installation setup on your machine and follow [this tutorial](https://flyabledev.github.io/FlyableDoc/#/get-started?id=_2-hello-world) to learn how to compile, link and run a Python script with Flyable. Alternatively, you can read the code in the main.py file to see how we do this.

# How does it get faster ?
Flyable does multiple things to generate efficient code but most of the performance gains come from the following:
- Native execution of the code
- Static function dispatch (enabling direct call and efficient inlining)
- Type tracking (When possible)
- Function specialization depending on the signature but also on the usage

# Supported platforms
Flyable only generates code for Windows 64 bits x86 for now. It will quickly be extended to Linux and Mac.

# How to use it ?
For now, Flyable is only available as a module that reads a Python file and outputs an object file. To run the output, the object file must be linked with any python39.lib file available in your Python installation. To run a Flyable made executable, it is required to have an active CPython installation setup on the machine.

Flyable is still in an early stage. We do not recommend full-scale usage at the moment.

# Plan
Our current efforts are primarily focused on stabilizing the compiler to support most Python syntax and optimize the most common Python use cases.

# Contributions

If you wish to, you can participate in this project in many ways:

- [Submit bugs and feature requests](https://github.com/FlyableDev/Flyable/issues)
- [Review pull requests](https://github.com/FlyableDev/Flyable/pulls)
- [Review the documentation](https://flyabledev.github.io/FlyableDoc/#/)
- Make a pull request to the code base

Feel free to contact us at contact@flyable.dev if you have any other concerns.
