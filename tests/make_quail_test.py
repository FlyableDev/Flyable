import os
from typing import Optional

from tests.quail.utils.trim import trim
from flyable import FLYABLE_VERSION


def create_new_quail_test_suite(name: str, add_place_holder_test: bool):
    """Creates a new folder with a body_<x>.py and a test_<x>.py file for Quail"""
    path = f"./unit_tests/{name}"
    try:
        os.makedirs(path, exist_ok=False)
    except OSError:
        print(
            f"The Quail test suite '{name}' already exists, if you wanted to add a new test, "
            f"use the 'add' command"
        )
        return
    with open(f"{path}/quailt_{name}.py", "w+") as body:
        if add_place_holder_test:
            body.write(
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
    print("Done!")

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


def create_new_quail_test():
    """
    In an already existing Quail test suite, creates a new Quail test in body_<x>.py
    and its corresponding test method in test_<x>.py if desired
    """


def get_value_of_arg(arg, command_args) -> Optional[str]:
    if arg in command_args:
        idx = command_args.index("--name") + 1
        if idx >= len(command_args):
            print(f"the {arg} command argument takes a value")
            return None
        return command_args[idx]
    return None


def handle_new(command_args: list[str]) -> Optional[dict]:
    name = command_args[0] if len(command_args) else None
    add_place_holder_test = "--blank" not in command_args

    if name is None:
        name = input("Name of the Quail test suite: ").strip()
        if not name:
            return None

    if add_place_holder_test is None:
        add_place_holder_test = (
                input("Add a Quail test place holder? ([Y], N)").lower() != "n"
        )

    return {"name": name, "add_place_holder_test": add_place_holder_test}


def cli():
    command: str
    command_args: list[str]

    res = input('|Quail> ')
    if len(res) > 0:
        command, *command_args = input("|Quail> ").split()
        command = command.lower()

        if command == "new":
            result = handle_new(command_args)
            if result is None:
                print("Creation of Quail test suite interrupted")
                return
            print("New Quail test suite description:")
            print("\n".join(f"- {name} = {value}" for name, value in result.items()))
            choice = input(
                "Do you want to proceed to create Quail test suite with those informations ([Y], N): "
            )
            if choice.lower() != "n":
                create_new_quail_test_suite(**result)
                return
            print("Creation of Quail test suite interrupted")

        elif command == "add":
            pass

        elif command == "quit":
            exit()

        else:
            print(f"Command '{command}' unknown, try again!")


def main():
    """"""
    print(
        trim(
            """
            Welcome to the Quail maker helper!
            How can I help you today?
            [new] Quail test suite
            [add] a new test to an existing test Quail test suite  
            [quit] to quit the program
            (you can interrupt the the program at any point by typing Ctrl+C)
            
            """
        )
    )
    while True:
        cli()


if __name__ == "__main__":
    main()
