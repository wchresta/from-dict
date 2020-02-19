import sys
import typing
from typing import Type, TypeVar, Optional, Mapping

PYTHON_VERSION = sys.version_info[:2]
IS_GE_PYTHON38 = PYTHON_VERSION >= (3, 8)  # Support for typing.get_args and typing.get_origin
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


if IS_GE_PYTHON38:
    def get_origin(t):
        return typing.get_origin(t)


    def get_args(t):
        return typing.get_args(t)
else:
    def get_origin(t):
        if hasattr(t, "__origin__"):
            return t.__origin__
        else:
            return None


    def get_args(t):
        if hasattr(t, "__args__"):
            return t.__args__
        else:
            return None


def type_check(v, t) -> None:
    """Raise RuntimeTypeError if given value does not agree with given type"""
    # This uses typing.get_args and typing.get_origin

    try:
        passed_isinstance = isinstance(v, t)
    except TypeError:  # Could happen if t is of sort List[x], etc.
        passed_isinstance = True

    if not passed_isinstance:
        raise FromDictTypeError([], t, type(v))

    origin = get_origin(t)
    type_args = get_args(t)
    if not origin or not type_args:
        return  # Give up

    if origin == typing.Union:
        for targ in type_args:
            try:
                type_check(v, targ)
                return  # Successfully type checked
            except FromDictTypeError:
                pass
        raise FromDictTypeError([], t, type(v))

    if not isinstance(v, origin):  # list ~ List[x], dict ~ Dict[x,y]
        raise FromDictTypeError([], t, type(v))

    if origin == list:
        targ = type_args[0]
        if not isinstance(v, list):
            raise FromDictTypeError([], t, type(v))
        for element in v:
            type_check(element, targ)


def get_constructor_type_hints(cls: Optional[Type]) -> Optional[Mapping[str, Type]]:
    if cls is None:
        return None

    return typing.get_type_hints(cls.__init__) or typing.get_type_hints(cls)


def from_dict(
        cls: Type[C],
        fd_from: Optional[dict] = None,
        fd_check_types: bool = False,
        fd_copy_unknown: bool = True,
        **overwrite_kwargs: Optional[dict]
) -> C:
    """Instantiate a class with parameters given by a dict.

    The dict is searched for fitting parameters. Keys that are not named like a parameter are ignored.

    If cls has generic type annotations with type arguments being classes themselves (like typing.List[SubClass]),
    the sub-classes are instantiated using the dictionary structure. Currently typing.List and typing.Mapping are
    supported.

    :param cls: Structure to be constructed from given dictionary.
    :param fd_from: Dictionary from which to read parameters.
    :param fd_check_types: Should type-checking at run-time be performed.
    :param fd_copy_unknown:
        Should additional keys not used in constructor be inserted into __dict__. This is on by default. This will only
        have an effect if constructed object has a __dict__.
    :param overwrite_kwargs: All additional keys will overwrite whatever is given in the dictionary.
    :return: Object of cls constructed with keys extracted from fd_from.
    """
    cls_constructor_argument_types = get_constructor_type_hints(cls)
    if not cls_constructor_argument_types:
        raise TypeError(f"Given class {cls} is not supported by from_dict")

    given_args = {}
    if fd_from:
        if not isinstance(fd_from, dict):
            raise TypeError(f"fd_from must be dict but was found to be {type(fd_from)}")
        given_args.update(fd_from)
    if overwrite_kwargs:
        given_args.update(overwrite_kwargs)

    ckwargs = {}
    for cls_argument_name, cls_argument_type in cls_constructor_argument_types.items():
        if cls_argument_name == "return" and cls_argument_type is None:
            # Ignore return argument
            continue

        try:
            given_argument = given_args[cls_argument_name]
        except KeyError:
            continue

        # Recursively from_dict attributes which are structures, too
        if (isinstance(given_argument, dict)
                and get_origin(cls_argument_type) in (dict, typing.Dict)  # in Python36, origin is Dict not dict
                and get_constructor_type_hints(get_args(cls_argument_type)[1])):
            # Dict[a,b]; we only support b being a structure.
            try:
                key_type, value_type = get_args(cls_argument_type)
                if fd_check_types:  # Perform type check on keys
                    all(type_check(k, key_type) for k in given_argument.keys())
                argument_value = {
                    k: from_dict(value_type, v, fd_check_types=fd_check_types)
                    for k, v in given_argument.items()
                }
            except FromDictTypeError as e:
                # Add location for better error message
                raise FromDictTypeError([cls_argument_name] + e.location, e.expected_type, e.found_type)
        elif isinstance(given_argument, dict) and get_constructor_type_hints(cls_argument_type):
            try:
                argument_value = from_dict(cls_argument_type, given_argument, fd_check_types=fd_check_types)
            except FromDictTypeError as e:
                # Add location for better error message
                raise FromDictTypeError([cls_argument_name] + e.location, e.expected_type, e.found_type)
        elif (isinstance(given_argument, list)
              and get_origin(cls_argument_type) in (list, typing.List)  # in Python36, origin is List not list
              and get_constructor_type_hints(get_args(cls_argument_type)[0])):
            try:
                list_var_type = get_args(cls_argument_type)[0]
                argument_value = [from_dict(list_var_type, x, fd_check_types=fd_check_types) for x in given_argument]
            except FromDictTypeError as e:
                # Add location for better error message
                raise FromDictTypeError([cls_argument_name] + e.location, e.expected_type, e.found_type)
        else:
            argument_value = given_argument

        if fd_check_types:
            try:
                type_check(argument_value, cls_argument_type)
            except FromDictTypeError as e:
                # Add location for better error message
                raise FromDictTypeError([cls_argument_name] + e.location, e.expected_type, e.found_type)

        ckwargs[cls_argument_name] = argument_value
        del given_args[cls_argument_name]

    created_object = cls(**ckwargs)

    # Check if created_object has a dictionary:
    if fd_copy_unknown and given_args and hasattr(created_object, "__dict__"):
        # Add the rest of the arguments to the dict, if possible.
        # Do not overwrite existing keys
        for arg, val in given_args.items():
            if arg not in created_object.__dict__:
                created_object.__dict__[arg] = val

    return created_object
