# Get Started

## 1. Install
<br />

Join the closed Beta by signing up and we'll send you a link to download the compiler!

<br />

<a href="https://share.hsforms.com/1F6ePZYJ6SxSFvBNecaQIKQ4woxi" style="
    text-decoration: none;
    color: white; 
    background-color: #13B3F2;
    border: none;
    border-radius: 25px;
    font-weight: 800;
    font-size: 15px;
    padding: 10px 20px;
    "><font size="4">Join the Beta</font></a>

<br />
<br />

## 2. Hello World!
<br />

In this section, we will go step by step over the process of compiling, linking and running a Python script with Flyable. We will suppose that we have a Python file named "test.py" that contains the following:

```Python
def main() :
    print("Hello World!")
```

Before you can start to play with Flyable, you will have to download it as well as the GCC compiler and make sure to add the path of the later to your PATH environment variable. 

<br />

Once the installation of Flyable is completed, create a new Python file and for the purpose of this example let's name it "main.py". You will first need to import Flyable and a few other tools.

```Python
import flyable.compiler as com
import flyable.tool.platform as plat
from subprocess import Popen, PIPE
from flyable import constants
from pathlib import Path
import platform

```

<br />

Now that this is done, let's create a function named "main" where we will do all the work. We first instatiate the compiler and indicate the Python file that we wish to compile, in this example it is "test.py". Next we tell the compiler in which folder we want it to output the files it will create. Make sure the folder already exists! In this example we ask the compiler to output the files in the folder "build" that can be found in the same folder than the file "main.py". Finally we ask the compiler to compile.


```Python
def main():
    print("Compiling....")
    compiler = com.Compiler()
    compiler.add_file("test.py")
    compiler.set_output_path("../build/" + plat.get_platform_folder() + "/output.o")
    Path("build").mkdir(parents=True, exist_ok=True)  # Make sur the folder exist
    compiler.compile()
```

<br />

After this is done, all we need to do is to link the different files to produce an executable and run this executable, but we first make sure that the compiler didn't produce any error:

```Python
def main():
    ...
    
    if not compiler.has_error():

        # Link the object file
        print("Linking.....")
        linker_args = ["gcc", "output.o", constants.LIB_FLYABLE_RUNTIME_PATH, constants.PYTHON_3_10_PATH]
        p = Popen(linker_args, cwd="..\\build\\" + plat.get_platform_folder())
        p.wait()
        if p.returncode != 0: raise Exception("Linking error")

        # Now run the code
        print("running...")
        p = Popen(["../build/" + plat.get_platform_folder() +
                   "/a.exe"], cwd="..\\build\\" + plat.get_platform_folder(), stdin=PIPE, stdout=PIPE)
        output, err = p.communicate()

        print("-------------------")
        print(output.decode())  # Print what the program outputted

        print("Application ended with code " + str(p.returncode))
```

As you can see, we assumed that you have Python 3.9 installed on your machine, but if you have another version just change "python39.lib" for "python38.lib" and "python3.9.a" for "python3.8.a" if you have Python 3.8 for example.

<br />

Finally, to run the main function simply add the following outside of the "main" function and run "main.py".

```Python
if __name__ == '__main__':
    main()
```

That's it! After a few seconds you should see the Hello World message print on your screen!
You can see the complete "main.py" file on [GitHub](https://github.com/FlyableDev/Flyable/blob/main/flyable/main.py).

<br />
<br />

## 3. Learn more
<br />

Take a look at the [FAQ](faq.md) to get answers to common questions, chat with the community on [Gitter](https://gitter.im/FlyableDev/community) and take a look at the code behind the compiler on [GitHub](https://github.com/FlyableDev/Flyable). You can also send us an email at <a href="mailto:contact@flyable.dev">contact@flyable.dev</a>!
