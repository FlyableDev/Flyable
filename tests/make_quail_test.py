import json
import os

from tests.quail.utils.trim import trim
from flyable import FLYABLE_VERSION
import click
from subprocess import Popen

HELP = "Welcome to the Quail maker helper!"


class QuailSuiteTestNameType(click.ParamType):
    name = "test_suite_name_type"

    def __init__(self):
        super().__init__()

    def convert(self, value, param, ctx):
        test_suite_name = value.strip()
        path = f"./tests/unit_tests/{test_suite_name}"
        if not os.path.exists(path):
            self.fail(
                f"The Quail test suite '{test_suite_name}' doesn't exist, if you wanted to create a new test suite, "
                f"use the 'new' command",
                param=param,
                ctx=ctx,
            )
        return test_suite_name


class QuailTestNameType(click.ParamType):
    name = "quail_test_name_type"

    def __init__(self):
        super().__init__()

    def convert(self, value, param, ctx):
        test_name = value.strip()
        if not test_name.replace("_", "").isalnum():
            self.fail(
                f"Invalid test name {test_name!r}. Test names must be alpha numerical (though _ are allowed)",
                param=param,
                ctx=ctx,
            )
        return test_name


@click.group(help=HELP)
def cli():
    pass


@cli.command(name="new")
@click.argument("name")
@click.option(
    "--blank",
    is_flag=True,
    help="Doesn't add a placeholder test in the test suite.",
    prompt="Do you want to add a placeholder test?",
    default=True,
)
@click.option(
    "--git-add",
    is_flag=True,
    help="Adds the files created to git",
    prompt="Do you want to add the file created to git?",
    default=True,
)
def create_new_quail_integration_test(name: str, blank: bool, git_add: bool):
    """
    For more information, write `Quail new --help`\n
    Creates a new Quail test suite <x> containing a folder with a quailt_<x>.py file and a test_<x>.py file.
    """
    path = f"./tests/unit_tests/{name}"
    try:
        os.makedirs(path, exist_ok=False)
    except OSError:
        print(
            f"The Quail test suite '{name}' already exists, if you wanted to add a new test, "
            f"use the 'add' command"
        )
        return
    with open(f"{path}/quailt_{name}.py", "w+") as body:
        msg = f'"""Module {name}"""\n\n'
        if blank:
            msg += (
                    trim(
                        f'''
                    # Quail-test:new
                    """
                    Name: YOUR_NAME
                    Flyable-version: {FLYABLE_VERSION}
                    Description: YOUR_DESCRIPTION
                    """
                    # Quail-test:start
                    "hello world!" == "hello world!"  # Quail-assert: True
                    # Quail-test:end
                    '''
                    )
                    + "\n"
            )
        body.write(msg)

    with open(f"{path}/test_{name}.py", "w+") as body:
        body.write(
            trim(
                """
                from tests.unit_tests.conftest import quail_runtimes_tester

                @quail_runtimes_tester
                def test_runtimes():
                    pass
                """
            )
            + "\n"
        )
    if git_add:
        Popen(f"git add ./{path}")
    click.echo(f"Quail test suite {name!r} created successfully!{u'🥳'}")


is_compile = False


def get_is_compile():
    return is_compile


def set_is_compile(_ctx, _self, choice):
    global is_compile
    if choice is None:
        return
    is_compile = choice == "compile"
    print(is_compile)


@cli.command(name="add")
@click.argument("test-suite-name", type=QuailSuiteTestNameType())
@click.option(
    "--test-name", prompt="Enter the name of your test", type=QuailTestNameType()
)
@click.option(
    "--mode",
    prompt="Enter the mode",
    default="runtime",
    type=click.Choice(["runtime", "compile", "both"]),
    callback=set_is_compile,
)
@click.option(
    "--add-tester",
    is_flag=True,
    prompt="Add a quail tester?",
    default=get_is_compile,
)
def add_test_to_test_suite(
        test_suite_name: str,
        test_name: str,
        mode: str = None,
        add_tester: bool = False,
):
    """
    For more information, write `Quail add --help`\n
    Adds a new Quail test to an already existing Quail test suite.
    """
    test_name = test_name.strip()
    if not test_name.replace("_", "").isalnum():
        print(
            f"Invalid test name {test_name!r}. Test names must be alpha numerical (though _ are allowed)"
        )
        return
    path = f"./tests/unit_tests/{test_suite_name}"
    if not os.path.exists(path):
        print(
            f"The Quail test suite '{test_suite_name}' doesn't exist, if you wanted to create a new test suite, "
            f"use the 'new' command"
        )
        return

    with open(f"{path}/quailt_{test_suite_name}.py", "a+") as body:
        msg = (
                trim(
                    f'''
                \n\n
                # Quail-test:new {mode if mode != "runtime" else ""}
                """
                Name: {test_name}
                Flyable-version: {FLYABLE_VERSION}
                Description: tests {test_name.replace("_", " ")}
                """
                # Quail-test:start
                
                # Quail-test:end
                '''
                )
                + "\n"
        )
        body.write(msg)

    if add_tester:
        with open(f"{path}/test_{test_suite_name}.py", "a+") as body:
            args = (
                "quail_test: QuailTest, stdout: StdOut"
                if mode != "compile"
                else "quail_results: CompilerResult"
            )
            body.write(
                trim(
                    f"""
                    \n\n
                    @quail_tester
                    def test_{test_name}({args}):
                        pass
                    """
                )
                + "\n"
            )
    click.echo(
        f"Quail test {test_name!r} created successfully in {test_suite_name!r}!{u'🥳'}"
    )

@cli.command(name="integration")
@click.argument("name")
@click.option(
    "--conf",
    is_flag=True,
    help="Puts nothing in the default quail.config.json",
    prompt="Do you want to create a default config file?",
    default=True,
)
@click.option(
    "--git-add",
    is_flag=True,
    help="Adds the files created to git",
    prompt="Do you want to add the file created to git?",
    default=True,
)
def create_new_quail_integration_test(name: str, conf: bool, git_add: bool):
    """
    For more information, write `Quail integration --help`\n
    Creates a new Quail integration test <x> containing a folder with a src folder, output folder and quail.config.json.
    """
    path = f"./tests/integration_tests/{name}"
    try:
        os.makedirs(path, exist_ok=False)
    except OSError:
        print(
            f"The Quail Integration test '{name}' already exists"
        )
        return
    
    os.mkdir(f"{path}/src")
    
    with open(f"{path}/quail.config.json", "w+") as body:
        if conf:
            content = json.dumps({
                'name': name,
                'description': f"Quail Integration test '{name}' for the flyable compiler",
                'main': 'main.py',
                "debug_flags": [],
                "logging": False
            }, indent=4)
        else:
            content = "{}"
        body.write(content)

    with open(f"{path}/src/main.py", "w+") as body:
        body.write('print("Hello World!")')
    
    os.mkdir(f"{path}/output")

    if git_add:
        Popen(f"git add ./{path}")
    click.echo(f"Quail integration test {name!r} created successfully!{u'🥳'}")