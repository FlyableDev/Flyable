import os

def get_platform_folder():
    if os.uname()[0] == "Windows":
        return "win64"
    elif os.uname()[0] == "Linux":
        return "linux64"