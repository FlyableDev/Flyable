import setuptools
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


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flyable",
    version="0.0.1",
    author="FlyableDev",
    author_email="contact@flyable.dev",
    description="Flyable is a Python compiler that generates optimized native code to improve the performance of Python workloads.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FlyableDev/Flyable",
    project_urls={
        "Bug Tracker": "https://github.com/FlyableDev/Flyable/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.11",
    package_data={
        "": [f"dyn_lib/{get_lib_folder_name()}/libflyableengine.{get_extension()}"]
    },
)
