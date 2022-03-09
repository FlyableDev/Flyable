from setuptools import setup, find_packages

setup(
    name="Quail",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    py_modules=["make_quail_test"],
    install_requires=["Click"],
    entry_points={"console_scripts": ["Quail = tests.make_quail_test:cli"]},
)
