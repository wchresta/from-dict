from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="from-dict",
    version="0.3.3",
    packages=find_packages(),
    author="Wanja Chresta",
    author_email="wanja.hs@chrummibei.ch",
    url="https://github.com/wchresta/from-dict",
    description="Create data structures from dictionaries.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[],
    tests_require=["pytest", "attr"],
)
