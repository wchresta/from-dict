{ pkgs ? import <nixpkgs> {} }:
let
  python-with-my-packages = pkgs.python3.withPackages (p: with p; [
    attrs
    black
    build
    pytest
    twine
    wheel
  ]);
in
python-with-my-packages.env
