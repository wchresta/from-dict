from setuptools import setup, find_packages

setup(
    name="from-dict",
    version="0.1",
    packages=find_packages(),
    author="Wanja Chresta",
    author_email="wanja.hs@chrummibei.ch",
    url="https://github.com/wchresta/from-dict",
    description="Create data structures from dictionaries.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[],
    tests_require=["pytest", "attr"],
)
