import flyable.compiler as com


def main():
    compiler = com.Compiler()
    compiler.add_file("test.py")
    compiler.compile()


if __name__ == '__main__':
    main()
