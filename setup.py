import setuptools

"""
Build script for PIP install. Requires built libraries to be in 
flyable/dyn_lib_folder (running build.py will build these and relocate them to this folder).
Uses local readme.md file to populate the pip install page on pypi.

Requires these pip packages to be installed:
* twine
* build

To build pip package run:
* python -m build (builds pip install files)
* python -m twine upload dist/* (uploads built package to pypi)
"""

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flyable",
    version="0.0.1.1",
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
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.11",
    package_data={
        "flyable.dyn_lib": [
            f"macos-arm64/*dylib",
            f"win64/*.dll",
            f"win64/*.dll.a",
            f"linux64/*.so",
        ]
    },
)
