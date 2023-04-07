from setuptools import setup, find_packages
from os import path
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='jextract',
    version='0.1.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'jx=jextract.run'
        ]
    },
    test_suite='test',
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)

