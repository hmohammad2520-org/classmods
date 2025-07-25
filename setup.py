from setuptools import find_packages, setup

setup(
    name='classmods',
    version='0.3.2',
    license="MIT",
    description='Simple mods for python classes.',
    author='hmohammad2520-org',
    author_email='hmohammad2520@gmail.com',
    url='https://github.com/hmohammad2520-org/classmods/',
    install_requires=[],
    packages=find_packages(exclude=['test', 'test.*']),
    include_package_data=True,
    zip_safe=False,
)