import setuptools


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
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.11",
    package_data={"": [f"dyn_lib/*/libflyableengine.*"]},
)
