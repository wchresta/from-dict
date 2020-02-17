from typing import Type, TypeVar, Optional, Mapping

C = TypeVar("C")


class FromDictTypeError(TypeError):
    def __init__(self, location, expected_type, found_type):
        self.location = location
        self.expected_type = expected_type
        self.found_type = found_type

    def __str__(self):
        return f"For \"{'.'.join(self.location)}\", expected {self.expected_type} but found {self.found_type}"

    def __repr__(self):
        return f"RuntimeTypeError({self.location!r}, {self.expected_type!r}, {self.found_type!r})"


def type_check(v, t) -> None:
    """Raise RuntimeTypeError if given value does not agree with given type"""

    try:
        passed_isinstance = isinstance(v, t)
    except TypeError:  # Could happen if t is of sort List[x], etc.
        passed_isinstance = True

    if not passed_isinstance:
        raise FromDictTypeError([], t, type(v))

    if repr(t).startswith("typing.List["):
        type_var = t.args[0]
        if not isinstance(v, list):
            raise FromDictTypeError([], t, type(v))
        for element in v:
            type_check(element, type_var)
    elif repr(t).startswith("typing.Union[") or repr(t).startswith("typing.Optional["):
        for type_var in t.args:
            try:
                type_check(v, type_var)
                return  # Successfully type checked
            except FromDictTypeError:
                pass
        raise FromDictTypeError([], t, type(v))


def get_field_types(cls: Type) -> Optional[Mapping[str, Type]]:
    try:
        # Support for attr and dataclasses
        return cls.__init__.__annotations__
    except AttributeError:
        pass

    # Support for NamedTuples
    try:
        return cls._field_types
    except AttributeError:
        pass

    return None


def from_dict(
        cls: Type[C],
        fd_from: Optional[dict] = None,
        fd_check_types: bool = False,
        fd_read_unknown: bool = True,
        **overwrite_kwargs: Optional[dict]
) -> C:
    """Read constructor parameters from a given dictionary.

    :param cls: Structure to be constructed from given dictionary.
    :param fd_from: Dictionary from which to read parameters.
    :param fd_check_types: Should type-checking at run-time be performed **EXPERIMENTAL**
    :param fd_read_unknown:
        Should additional keys not used in constructor be inserted into __dict__. This is on by default. This will only
        have an effect if constructed object has a __dict__.
    :param overwrite_kwargs: All additional keys will overwrite whatever is given in the dictionary.
    :return: Object of cls constructed with keys extracted from fd_from.
    """
    field_types = get_field_types(cls)
    if not field_types:
        raise TypeError(f"Given class {cls} is not supported by from_dict")

    given_args = {}
    if fd_from:
        given_args.update(fd_from)
    if overwrite_kwargs:
        given_args.update(overwrite_kwargs)

    ckwargs = {}
    for argument_name, argument_type in field_types.items():
        if argument_name == "return" and argument_type is None:
            # Ignore return argument
            continue

        try:
            given_argument = given_args[argument_name]
        except KeyError:
            continue

        # Recursively from_dict attributes which are structures, too
        if isinstance(given_argument, dict) and get_field_types(argument_type):
            try:
                argument_value = from_dict(argument_type, given_argument, fd_check_types=fd_check_types)
            except FromDictTypeError as e:
                # Add location for better error message
                raise FromDictTypeError([argument_name] + e.location, e.expected_type, e.found_type)
        else:
            argument_value = given_argument

        if fd_check_types:
            try:
                type_check(argument_value, argument_type)
            except FromDictTypeError as e:
                # Add location for better error message
                raise FromDictTypeError([argument_name] + e.location, e.expected_type, e.found_type)

        ckwargs[argument_name] = argument_value
        del given_args[argument_name]

    created_object = cls(**ckwargs)

    # Check if created_object has a dictionary:
    if fd_read_unknown and given_args and hasattr(created_object, "__dict__"):
        # Add the rest of the arguments to the dict, if possible.
        created_object.__dict__.update(given_args)

    return created_object
