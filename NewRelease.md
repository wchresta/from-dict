# New release instructions

```
$ nix develop
$ rm dist/*
$ python3 setup.py sdist bdist_wheel
$ # Ensure ~/.pypirc is set up correctly
$ python -m twine upload --repository from-dict-test dist/*
$ # Inspect package
$ python -m twine upload --repository from-dict dist/*
```

