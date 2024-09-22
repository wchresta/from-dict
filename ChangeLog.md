# Version 0.4.2 - 2024-09-21
* Bug fix for generic classes

# Version 0.4.1 - 2014-03-07
* Officially supporting Python 3.12
* Fixing bug with unions and data-classes that have default values
  
# Version 0.4.0 - 2023-06-16
* Adding basic support for Literal type hints
* Adding `fd_error_on_unknown` argument
* Drop support for 3.7

# Version 0.3.3 - 2022-11-27
* Adding basic support for classes that inherit from
  classes that inherit from `Generic[...]`

# Version 0.3.2 - 2022-11-13
* Adding support for classes that inherit from `Generic[...]`

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

