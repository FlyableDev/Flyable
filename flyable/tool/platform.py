import platform


def get_platform_folder():
    if platform.system() == "Windows":
        return "win64"
    elif platform.system() == "Linux":
        return "linux64"
    elif platform.system() == "Darwin" and platform.machine() == "arm64":
        return "macos-arm64"
    else:
        raise NotImplemented(platform.system() + platform.system())
