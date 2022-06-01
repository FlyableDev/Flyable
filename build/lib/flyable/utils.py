import platform

def get_lib_folder_name() -> str:
    system = platform.system()
    if system == "Windows":
        return "win64"

    if system == "Darwin":
        return "macos-arm64"

    if system == "Linux":
        return "linux64"


def get_extension() -> str:
    system = platform.system()
    if system == "Windows":
        return "dll"

    if system == "Darwin":
        return "dylib"

    if system == "Linux":
        return "so"
