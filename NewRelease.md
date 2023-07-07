# New release instructions

```
$ nix develop
$ rm dist/*
$ python3 setup.py sdist bdist_wheel
$ python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
$ # Inspect package
$ python -m twine upload dist/*
```

