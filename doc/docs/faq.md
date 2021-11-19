# FAQ

Here are the most frequently asked questions about Flyable. They are organised into different categories. 
You can click on links provided in the answers to be redirected to more detailed documentation on the subject. 
If you don't find the answers you are looking for, don't hesitate to communicate with our team at contact@flyable.dev.

<br />

## Introduction

### What is Flyable?

Flyable is an ahead-of-time compiler for Python code. It takes Python code, analyses, optimizes, and transforms it directly to machine code. Doing so allows Flyable to speed up any Python code with little to no modification.

### How can Flyable be useful for me / Why should I use Flyable?

If you're looking to significantly increase performance on an existing Python project with little to no effort, 
Flyable is the solution! Speeding up your Python code will reduce server workload while allowing you to iterate faster during the development of your software. Also, by reducing the latency of your software, the people using it will get a better experience. 

### How do I get started?

It's simple! Visit the [download page](get-started.md#_1-install), and follow the instructions.

### Is Flyable free?

Yes it is! Flyable is open source and is licensed under the GNU Affero General Public License v3.0.

### Can I get commercial support?

Of course! For more information you can contact the team directly at contact@flyable.dev.

<br />
<br />

## General Python Compatibility

### How does Flyable work with Python?

Flyable compiles Python code into executable files. 
To do this, it lexes and parses the Python code, then uses a type discovery algorithm and finally applies optimisations before generating the desired output.

### Can I use any Python libraries / frameworks / modules?

Yes. Flyable works closely with the Python interpreter (CPython) to ensure that any external code will run exactly the same. This way developers can still enjoy their favorite libraries with the boost given by Flyable. In a near future, Flyable will also be able to compile any external libraries to extend the performance boost to them.

### Can my Python code call a Flyable module?

Not for now. Right now, Flyable only creates static modules to facilitate calls from Flyable to Flyable and calls from Flyable to Python. We do expect to make it work in the future.

<br />
<br />

## Syntax

### Do I need to change any of my code?

Ideally no, but realistically Flyable is still young and will sometimes require a few changes. Some syntaxic features are still missing right now, but this is a temporary situation, we are working on it.

### Could I compile my pre-existing Python code?

Sure, as long as it stays in the bounds of the Python functionalities that Flyable supports right now.

<br />
<br />

## Performance & General Usage

### What is the expected speedup?

For now, Flyable is expected to speed up your entire software execution time by 20-30%. This number highly varies depending on what the code is doing and how it's written. For specific algorithms Flyable can boost Python to make it up to 70 times faster. 
Also, although Flyable supports Python modules, it doesn't speed them up for now so only the parts of the code that do not depend on Python modules will be accelerated by Flyable.

### How does Flyable make Python faster and more lightweight?

The compiler applies strong optimization to your Python code before generating a native executable on Windows.

### How does the Flyable compiler work?

Flyable lexes and parses the Python code with the help of the Python ast module which generates an abstract syntax tree. Then a type discovery algorithm is applied and a code generator produces LLVM intermediate representation which is fed to LLVM. LLVM then applies additional optimizations and produces an executable for the desired architecture.

### What architectures can I run Flyable on?

Flyable produces x86 instructions that run on Windows 64 bits. Support for Linux and MacOS is planned. ARM support is also planned. 32 bits support isn’t planned in the near future.

### What does Flyable produce?

Flyable produces an executable file that can directly be launched. The executable file will find the Python installation on the setup to find any external modules required.
We're also planning to offer the possibility to package all the required modules and files into the executable to remove the need to have an active Python installation to run Flyable made software.

<br />
<br />

## Development

### Can I be a part of Flyable’s development process?

Yes! To download Flyable, visit the [download page](get-started.md#_1-install). To contribute to Flyable, visit [Flyable’s GitHub repository](https://github.com/FlyableDev/Flyable).

### Is Flyable open-source?

Yes it is! You can see the code [here](https://github.com/FlyableDev/Flyable).

<br />
<br />

## Community

### How does Flyable help with data science?

Flyable helps you develop more performant Python code. Our benchmarks show that Flyable makes Python code up to 70x faster while using 80% less memory. This helps developers be more efficient and build better software and it helps organizations cut operating expenses.

### How can I connect with the Flyable team/community?

You can connect with the Flyable team on [Twitter](https://twitter.com/FlyableDev) and [LinkedIn](https://www.linkedin.com/company/flyable) and you can send us a message at contact@flyable.dev. You can also connect with the community on [Discord](https://discord.gg/tquHUe9Q89).
