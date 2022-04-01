![Flyable](https://www.flyabledev.com/images/logo_flyable.svg)

<p align="center">
    <!-- AGPL licence -->
    <a href="https://www.gnu.org/licenses/agpl-3.0">
        <img src="https://img.shields.io/badge/License-AGPL_v3-blue.svg" alt="License: AGPL v3">
    </a>
    <!-- LLVM version -->
    <a href="https://releases.llvm.org/">
        <img src="https://img.shields.io/badge/LLVM-v13-blue" alt="LLVM version">
    </a>
    <!-- Python version -->
    <a href="">
        <img src="https://img.shields.io/badge/python-3.11-blue" alt="Python version">
    </a>
    <!-- Discord -->
    <a href="https://discord.gg/tquHUe9Q89">
        <img src="https://img.shields.io/discord/907997505105559603" alt="Discord">
    </a>
    <!-- Twitter -->
    <a href="https://twitter.com/intent/follow?screen_name=FlyableDev">
        <img src="https://img.shields.io/twitter/url?label=Follow&style=social&url=https%3A%2F%2Ftwitter.com%2FFlyableDev" alt="Twitter Follow">
    </a>
</p>

<p align="center"><i>A Python compiler for highly performant code.</i></p>
<p align="center"><i>Check <a href="https://flyable.dev/">the website</a> for more information.</i></p>

## Introduction
Welcome to the official Flyable GitHub repository! 😊🎉🥳

Flyable is a Python ahead-of-time compiler that generates optimized native code to decrease Python workloads. 
<!--Based on benchmarks from [The Python Benchmark Suite](https://github.com/python/pyperformance), Flyable delivers on average a 2 times speedup without having to modify your code. -->

Flyable works hand in hand with the interpreter in the sense that when Flyable can compile a function 
or method it does so and the interpreter executes that compiled function at runtime and otherwise Flyable lets the interpreter 
interpret this function or method.

## Benchmarks
Detailed benchmarks to come soon! You can see previous benchmarks [here](https://www.flyabledev.com/benchmarks.html).

## Supported platforms
Flyable currently supports the following OS and architectures:

🪟 x86 instructions that run on Windows 64 bits.

🍎 ARM instructions that run on MacOS 64 bits. 

🐧 x86 instructions that run on Linux 64 bits.

32 bits support isn’t planned in the near future.

## Getting Started
All you will need is a working CPython installation (do not run Flyable inside a venv) and some Python code to compile. Clone the repository on your computer and you will be ready to start using Flyable! You can read the code in [main.py](https://github.com/FlyableDev/Flyable/blob/main/main.py) to see an example of how to select the file to compile.
<!-- add link to use the plugins when it's available -->

## Related projects
See [Quail](https://github.com/FlyableDev/Flyable/blob/main/tests/quail/docs/README.md): the unit testing utility for the Flyable compiler

## How does it get faster ?
Flyable does multiple things to generate efficient code but most of the performance gains come from the following:
- Native execution of the code
- Static function dispatch (enabling direct call and efficient inlining)
- Type tracking (When possible)
- Function specialization depending on the signature but also on the usage

## Roadmap
Our work is currently focused on integrating new optimizations and getting the compiler to support more syntactic features in order to increase the  proportion of functions and methods that are compiled. 🛣️🚗

<!--You can see a detailed roadmap [here](https://github.com/FlyableDev/Flyable/projects/1).-->

## Contributions

If you want to participate and/or support the active development of Flyable:

- [Add a GitHub star](https://github.com/FlyableDev/Flyable/stargazers) to the project. ⭐
- Tweet about the project on [your Twitter](https://twitter.com/intent/tweet?text=%40FlyableDev%20makes%20a%20Python%20ahead-of-time%20compiler%20that%20uses%20LLVM%20to%20generate%20efficient%20native%20code.%20It%27s%20fully%20compatible%20with%20the%20Python%20syntax.%20Take%20a%20look%20at%20the%20GitHub%20repo%3A%20https%3A%2F%2Fbit.ly%2F35XN7Tc).
- [Submit bugs and feature requests](https://github.com/FlyableDev/Flyable/issues). 🐞
- [Review or make pull requests](https://github.com/FlyableDev/Flyable/pulls). If you would like to work on an issue, please let us know by writing a comment 
in the issue you are interested in. We have identified [good first issues](https://github.com/FlyableDev/Flyable/labels/good%20first%20issue) 
for issues we believe are well suited for people who want to start tackling issues.

## Keep in touch
- If you have any technical question, you can write a question on Stack Overflow. 
- Follow us on [Twitter](https://twitter.com/intent/follow?screen_name=FlyableDev) or [LinkedIn](https://www.linkedin.com/company/flyable).
- Feel free to contact us on [Discord](https://discord.gg/tquHUe9Q89) or at contact@flyable.dev if you have any other concerns.

## Licence
Flyable is licensed under the GNU Affero General Public License v3.0 .

## Acknowledgments
🐉 LLVM is one of the powerful optimizing machines running under the hood.

🐍 CPython is ubiquitous in this project.

🐃 GCC is linking everything tightly.