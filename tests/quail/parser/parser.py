from os import path

from tests.quail.parser.quail_test_parser import QuailTestParser


def parse_quailt_file(file_path: str):
    test_parser = QuailTestParser(path.basename(file_path))

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        test_parser.parse_line(line)

    for test in test_parser.parsed_tests:
        test.is_valid_or_raise()

    return {test.name: test for test in test_parser.parsed_tests}
