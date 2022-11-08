{ pkgs ? import <nixpkgs> {} }:
let
  python-with-my-packages = pkgs.python3.withPackages (p: with p; [
    build
    attrs
    pytest
    black
  ]);
in
python-with-my-packages.env
