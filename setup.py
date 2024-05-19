"""
This model is used to create the package
"""

from setuptools import setup


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='djangorestframework-hybridrouter',
    version='0.1.5',
    packages=[
        'hybridrouter',
    ],
    install_requires=[
        'Django',
        'djangorestframework',
    ],
    description='A package to regsiter viewsets and views in the same router',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Made by enzo_frnt from a ',
    url='https://github.com/enzofrnt/djangorestframework-hybridrouter',
    keywords=["Django", "Django REST Framework", "viewsets", "views", "router", "view", "viewset"],
    test_suite='test',
)
