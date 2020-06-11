from setuptools import setup, find_packages
import sys


setup(
    name="asyncua_utils",
    version="0.1",
    description="utilities for using the python opcua implementation",
    author="Joey Faulkner",
    author_email="joeymfaulkner@gmail.com",
    packages=find_packages(),
    provides=["asyncua_utils"],
)
