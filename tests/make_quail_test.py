import os

from tests.quail.utils.trim import trim
from flyable import FLYABLE_VERSION
import click


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
    "--blank", is_flag=True, help="Doesn't add a placeholder test in the test suite."
)
def create_new_quail_test_suite(name: str, blank: bool):
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
        msg = f"'''Module {name}'''\n\n"
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
    click.echo(f"Quail test suite {name!r} created successfully!🥳")


@cli.command(name="add")
@click.argument("test_suite_name", type=QuailSuiteTestNameType())
@click.option(
    "--test_name", prompt="Enter the name of your test", type=QuailTestNameType()
)
@click.option(
    "--mode",
    prompt="Enter the mode",
    default="runtime",
    type=click.Choice(["runtime", "compile", "both"]),
)
@click.option(
    "--add_tester",
    is_flag=True,
    confirmation_prompt="Add a quail tester?",
    default=False,
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
        f"Quail test {test_name!r} created successfully in {test_suite_name!r}!🥳"
    )
