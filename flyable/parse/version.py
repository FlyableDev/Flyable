import enum


class PythonVersion(enum.IntEnum):
    VERSION_3_10 = 0
    VERSION_3_11 = 1


__CURRENT_VERSION = PythonVersion.VERSION_3_11


def get_python_version():
    return __CURRENT_VERSION
