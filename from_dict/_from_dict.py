import sys
import typing
import functools
from dataclasses import is_dataclass
from typing import Type, TypeVar, Optional, Mapping, Union, Callable, Any

PYTHON_VERSION = sys.version_info[:2]
# Support for typing.get_args and typing.get_origin
IS_GE_PYTHON38 = PYTHON_VERSION >= (3, 8)
C = TypeVar("C")


class FromDictTypeError(TypeError):
    def __init__(self, location, expected_type, found_type):
        self.location = location
        self.expected_type = expected_type
        self.found_type = found_type

    def __str__(self):
        return f"For \"{'.'.join(self.location)}\", expected {self.expected_type} but found {self.found_type}"

    def __repr__(self):
        return f"FromDictTypeError({self.location!r}, {self.expected_type!r}, {self.found_type!r})"


class NamespaceTypes:
    def __init__(self, global_ns: Optional[dict], local_ns: Optional[dict]) -> None:
        """We only care about the entries with classes in them.
        For local namespaces if a class is defined inline it will not compare
        equal to itself.
        """

        def get_types(ns: dict):
            items = ((k, v) for k, v in ns.items() if isinstance(v, type))
            return frozenset(items)

        self._global_types = None if global_ns is None else get_types(global_ns)
        self._local_types = None if local_ns is None else get_types(local_ns)
        self._hash = hash((self._global_types, self._local_types))

    @property
    def global_types(self) -> Optional[dict]:
        return None if self._global_types is None else dict(self._global_types)

    @property
    def local_types(self) -> Optional[dict]:
        return None if self._local_types is None else dict(self._local_types)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, NamespaceTypes):
            return False

        return (
            self is o
            or self._hash == o._hash
            and self._global_types == o._global_types
            and self._local_types == o._local_types
        )


if IS_GE_PYTHON38:
    from typing import get_origin, get_args
else:

    def get_origin(tp) -> Optional[type]:
        if hasattr(tp, "__origin__"):
            return tp.__origin__
        else:
            return None

    def get_args(tp) -> tuple:
        if hasattr(tp, "__args__"):
            return tp.__args__
        else:
            return ()


def type_check(check_stack: list, v: Any, t: type) -> None:
    """Raise FromDictTypeError if given value does not agree with given type"""
    # This uses typing.get_args and typing.get_origin
    def location():
        return ["".join(check_stack)]

    try:
        passed_isinstance = isinstance(v, t)
    except TypeError:  # Could happen if t is of sort List[x], etc.
        passed_isinstance = True

    if not passed_isinstance:
        raise FromDictTypeError(location(), t, type(v))

    origin = get_origin(t)
    type_args = get_args(t)
    if not origin or not type_args:
        return  # Give up

    if origin == Union:
        for targ in type_args:
            try:
                type_check(check_stack, v, targ)
                return  # Successfully type checked
            except FromDictTypeError:
                pass
        raise FromDictTypeError(location(), t, type(v))

    if not isinstance(v, origin):  # list ~ List[x], dict ~ Dict[x,y]
        raise FromDictTypeError(location(), t, type(v))

    if origin == list:
        targ = type_args[0]
        if not isinstance(v, list):
            raise FromDictTypeError(location(), t, type(v))
        for i, element in enumerate(v):
            type_check(check_stack + [f"[{i}]"], element, targ)
    elif origin == dict:
        targ = type_args[0]
        if not isinstance(v, dict):
            raise FromDictTypeError(location(), t, type(v))
        for k, val in v.items():
            if not isinstance(k, type_args[0]):
                raise FromDictTypeError(location(), t, type(v))
            type_check(check_stack + [f"[{k!r}]"], val, type_args[1])


def is_attr(cls):
    # similar to attrs.has()
    return hasattr(cls, "__attrs_attrs__")


@functools.lru_cache(100)
def get_constructor_type_hints(
    cls: Optional[Type],
    ns_types: NamespaceTypes,
) -> Mapping[str, Type]:
    if cls is None:
        return {}

    hints = typing.get_type_hints(
        cls.__init__, ns_types.global_types, ns_types.local_types
    ) or typing.get_type_hints(cls, ns_types.global_types, ns_types.local_types)
    return {k: v for k, v in hints.items() if (k != "return" and v is not type(None))}


def resolve_str_forward_ref(
    type_or_name: Union[str, Type],
    cls: Type,
    ns_types: NamespaceTypes,
) -> Type:
    """starting in Python 3.9 types can be list['class-forward-reference'].
    The inner string is not resolved like when typing.List['class-forward-reference'] is used.
    This helper will attempt to resolve these string forward references.
    """
    if not isinstance(type_or_name, str):
        return type_or_name
    return _resolve_str_forward_ref(type_or_name, cls, ns_types)


@functools.lru_cache(100)
def _resolve_str_forward_ref(
    type_or_name: str,
    cls: Type,
    ns_types: NamespaceTypes,
) -> Type:
    if ns_types.local_types and type_or_name in ns_types.local_types:
        return ns_types.local_types[type_or_name]
    elif ns_types.global_types and type_or_name in ns_types.global_types:
        return ns_types.global_types[type_or_name]
    elif hasattr(sys.modules[cls.__module__], type_or_name):
        return getattr(sys.modules[cls.__module__], type_or_name)
    else:
        raise TypeError(f"Type hint '{type_or_name}' could not be resolved")


def from_dict(
    cls: Type[C],
    fd_from: Optional[dict] = None,
    fd_check_types: bool = False,
    fd_copy_unknown: bool = True,
    fd_global_ns: Optional[dict] = None,
    fd_local_ns: Optional[dict] = None,
    **overwrite_kwargs: Any,
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
    :param fd_global_ns: global namespace to help with handling of forward references encoded as string literals
    :param fd_local_ns: local namespace to help with handling of forward references encoded as string literals
    :param overwrite_kwargs: All additional keys will overwrite whatever is given in the dictionary.
    :return: Object of cls constructed with keys extracted from fd_from.
    """
    ns_types = NamespaceTypes(fd_global_ns, fd_local_ns)
    given_args = {}
    if fd_from:
        if not isinstance(fd_from, dict):
            raise TypeError(f"fd_from must be dict but was found to be {type(fd_from)}")
        given_args.update(fd_from)
    if overwrite_kwargs:
        given_args.update(overwrite_kwargs)
    return _from_dict_inner(cls, given_args, fd_check_types, fd_copy_unknown, ns_types)


def _from_dict_inner(
    cls: Type[C],
    given_args: Union[dict, Any],
    fd_check_types: bool,
    fd_copy_unknown: bool,
    ns_types: NamespaceTypes,
) -> C:
    if not isinstance(given_args, dict):
        return given_args

    _get_constructor_type_hints = functools.partial(
        get_constructor_type_hints, ns_types=ns_types
    )
    _resolve_str_forward_ref = functools.partial(
        resolve_str_forward_ref, cls=cls, ns_types=ns_types
    )
    _from_dict = functools.partial(
        _from_dict_inner,
        fd_check_types=fd_check_types,
        fd_copy_unknown=fd_copy_unknown,
        ns_types=ns_types,
    )

    cls_constructor_argument_types = _get_constructor_type_hints(cls)
    if not cls_constructor_argument_types:
        raise TypeError(f"Given class {cls} is not supported by from_dict")

    ckwargs = {}
    for cls_argument_name, cls_argument_type in cls_constructor_argument_types.items():
        try:
            given_argument = given_args[cls_argument_name]
        except KeyError:
            continue

        try:
            # Recursively from_dict attributes which are structures, too
            argument_value = handle_item(
                _get_constructor_type_hints,
                _resolve_str_forward_ref,
                _from_dict,
                cls_argument_type,
                given_argument,
            )
        except FromDictTypeError as e:
            # Add location for better error message
            e = FromDictTypeError(
                [cls_argument_name] + e.location, e.expected_type, e.found_type
            ).with_traceback(sys.exc_info()[2])
            raise e from None

        if fd_check_types:
            type_check([cls_argument_name], argument_value, cls_argument_type)

        ckwargs[cls_argument_name] = argument_value

    created_object = cls(**ckwargs)

    # Check if created_object has a dictionary:
    if fd_copy_unknown and given_args and hasattr(created_object, "__dict__"):
        # Add the rest of the arguments to the dict, if possible.
        # Do not overwrite existing keys
        for arg, val in given_args.items():
            if arg not in ckwargs and arg not in created_object.__dict__:
                created_object.__dict__[arg] = val

    return created_object


def handle_item(
    _get_constructor_type_hints: Callable[[Type], Mapping[str, Type]],
    _resolve_str_forward_ref,
    _from_dict: Callable[[Type[C], dict], C],
    cls_argument_type: Type,
    given_argument: Any,
):
    """Handles an item who's type has not been determined yet"""
    if isinstance(given_argument, dict):
        return handle_dict_argument(
            _get_constructor_type_hints,
            _resolve_str_forward_ref,
            _from_dict,
            cls_argument_type,
            get_args(cls_argument_type),
            given_argument,
        )
    elif isinstance(given_argument, list):
        return handle_list_argument(
            _get_constructor_type_hints,
            _resolve_str_forward_ref,
            _from_dict,
            cls_argument_type,
            get_args(cls_argument_type),
            given_argument,
        )
    # TODO: Add support for Tuple?
    else:
        return given_argument


def handle_dict_argument(
    _get_constructor_type_hints: Callable[[Type], Mapping[str, Type]],
    _resolve_str_forward_ref,
    _from_dict: Callable[[Type[C], dict], C],
    cls_argument_type: Type,
    cls_arg_type_args: tuple,
    given_argument: dict,
) -> object:
    """This is called when the given argument is an instance of 'dict'"""

    # Empty dictionary. Does not matter what the items are.
    if not given_argument:
        return given_argument

    # Common case: The expected type is a dataclass or attr
    if is_dataclass(cls_argument_type) or is_attr(cls_argument_type):
        return _from_dict(cls_argument_type, given_argument)

    cls_argument_origin = get_origin(cls_argument_type)

    # Expected type is dictionary object with type hints
    if cls_argument_origin is dict:
        # Dict[a,b]; we only support b being a structure.
        value_type = _resolve_str_forward_ref(cls_arg_type_args[1])

        # The dictionary value's type is either a dataclass or attr class
        # Check this first because it is a common case and a fast check
        if is_dataclass(value_type) or is_attr(value_type):
            return {k: _from_dict(value_type, v) for k, v in given_argument.items()}

        # The dictionary value's type can be anything so leave it as it is.
        if value_type is Any:
            return given_argument  # TODO: return a copy?

        # A generic type with type-hints
        value_type_origin = get_origin(value_type)
        if value_type_origin is not None:
            if value_type_origin in (dict, list):
                return {
                    k: handle_item(
                        _get_constructor_type_hints,
                        _resolve_str_forward_ref,
                        _from_dict,
                        value_type,
                        v,
                    )
                    for k, v in given_argument.items()
                }

            if value_type_origin is Union:
                return {
                    k: _handle_union(
                        _get_constructor_type_hints,
                        _resolve_str_forward_ref,
                        _from_dict,
                        value_type,
                        v,
                    )
                    for k, v in given_argument.items()
                }

        # Any object that has type-hints in the constructor
        if _get_constructor_type_hints(value_type):
            return {k: _from_dict(value_type, v) for k, v in given_argument.items()}

        # The dictionary value's type does not need to be converted
        # Examples: int, str, or dict (with no type-hints)
        return given_argument  # TODO: return a copy?

    # Expected type is a union of multiple types
    if cls_argument_origin is Union:
        return _handle_union(
            _get_constructor_type_hints,
            _resolve_str_forward_ref,
            _from_dict,
            cls_argument_type,
            given_argument,
        )

    # Expected type can be anything so leave it as it is.
    if cls_argument_type is Any:
        return given_argument

    # Expected type is any object has type-hints in the constructor
    if _get_constructor_type_hints(cls_argument_type):
        return _from_dict(cls_argument_type, given_argument)

    # The argument's type does not need to be converted
    # Should only be be a dict (with no type-hints)
    # or the expected type is one that does not have type hints
    return given_argument  # TODO: return a copy?


def handle_list_argument(
    _get_constructor_type_hints: Callable[[Type], Mapping[str, Type]],
    _resolve_str_forward_ref,
    _from_dict: Callable[[Type[C], dict], C],
    cls_argument_type: Type,
    cls_arg_type_args: tuple,
    given_argument: list,
) -> object:
    """This is called when the given argument is an instance of 'list'"""

    # Empty list. Does not matter what the elements are.
    if not given_argument:
        return given_argument

    cls_argument_origin = get_origin(cls_argument_type)

    # Expected type is list object with type hints
    if cls_argument_origin is list:
        element_type = _resolve_str_forward_ref(cls_arg_type_args[0])

        # The list's element's type is either a dataclass or attr class
        # Check this first because it is a common case and a fast check
        if is_dataclass(element_type) or is_attr(element_type):
            return [_from_dict(element_type, x) for x in given_argument]

        # The list element's type can be anything so leave it as it is.
        if element_type is Any:
            return given_argument  # TODO: return a copy?

        # A generic type with type-hints
        element_type_origin = get_origin(element_type)
        if element_type_origin is not None:
            if element_type_origin in (dict, list):
                return [
                    handle_item(
                        _get_constructor_type_hints,
                        _resolve_str_forward_ref,
                        _from_dict,
                        element_type,
                        element,
                    )
                    for element in given_argument
                ]

            if get_origin(element_type) is Union:
                return [
                    _handle_union(
                        _get_constructor_type_hints,
                        _resolve_str_forward_ref,
                        _from_dict,
                        element_type,
                        v,
                    )
                    for v in given_argument
                ]

        # Any object that has type-hints in the constructor
        if _get_constructor_type_hints(element_type):
            return [_from_dict(element_type, x) for x in given_argument]

        # The list value's type does not need to be converted
        # Examples: int, str, or dict (with no type-hints)
        return given_argument  # TODO: return a copy?

    # Expected type is a union of multiple types
    if cls_argument_origin is Union:
        return _handle_union(
            _get_constructor_type_hints,
            _resolve_str_forward_ref,
            _from_dict,
            cls_argument_type,
            given_argument,
        )

    return given_argument


def _handle_union(
    _get_constructor_type_hints: Callable[[Type], Mapping[str, Type]],
    _resolve_str_forward_ref,
    _from_dict: Callable[[Type[C], dict], C],
    cls_argument_type: Type,
    given_argument: Any,
):
    """This is called when the expected type is a union of multiple types"""
    if isinstance(given_argument, dict):
        for arg_type in get_args(cls_argument_type):
            if arg_type is type(None):
                continue
            if get_origin(arg_type) is dict:
                return handle_dict_argument(
                    _get_constructor_type_hints,
                    _resolve_str_forward_ref,
                    _from_dict,
                    arg_type,
                    get_args(arg_type),
                    given_argument,
                )
            required_keys = _get_constructor_type_hints(arg_type)
            if all(k in required_keys for k in given_argument):
                try:
                    return _from_dict(arg_type, given_argument)
                except TypeError:
                    pass
        return given_argument

    if isinstance(given_argument, list):
        for arg_type in get_args(cls_argument_type):
            if arg_type is type(None):
                continue
            if get_origin(arg_type) is list:
                try:
                    return handle_list_argument(
                        _get_constructor_type_hints,
                        _resolve_str_forward_ref,
                        _from_dict,
                        arg_type,
                        get_args(arg_type),
                        given_argument,
                    )
                except TypeError:
                    pass
        return given_argument

    return given_argument
