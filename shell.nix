{ pkgs ? import <nixpkgs> {} }:
let
  python-with-my-packages = pkgs.python3.withPackages (p: with p; [
    attrs
    pytest
  ]);
in
python-with-my-packages.env
