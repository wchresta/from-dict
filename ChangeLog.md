# Version 0.3.1 - 2022-11-08
* Improvements to type error messages.
* Expand support of complex types.

# Version 0.3 - 2022-08-11
* Drop support for 3.6
* Fixing a bug where fields of type `Dict[...]` were not being parsed
  properly if the values were primitive types (thanks jcal-15).
* Add internal caching, making repeated `from_dict `faster (thanks jcal-15).

# Version 0.2.1 - 2022-06-19
* Add support for forward-referenced types (thanks jcal-15)

# Version 0.2 - 2020-02-19
* Rewrite type-check
* Rename `fd_*` arguments [Breaking change]
* Add support for `Dict[a,b]`
* Bunch of bug fixes

