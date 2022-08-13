import sys
import typing
import functools
from dataclasses import dataclass
from typing import Type, TypeVar, Optional, Mapping, Union, Callable, Any

PYTHON_VERSION = sys.version_info[:2]
IS_GE_PYTHON38 = PYTHON_VERSION >= (
    3,
    8,
)  # Support for typing.get_args and typing.get_origin
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


@dataclass(frozen=True)
class CommonParams:
    check_types: bool
    global_ns: Optional[dict]
    local_ns: Optional[dict]


class ArgumentState:
    def __init__(
        self, name: str, type: Type, value: Any, cls: Type, common: CommonParams
    ):
        self.name = name
        self.type = type
        self.value = value
        self._resolve_str_forward_ref = functools.partial(
            resolve_str_forward_ref,
            cls=cls,
            global_ns=common.global_ns,
            local_ns=common.local_ns,
        )
        self._origin: Optional[Type] = None
        self._args: Optional[tuple] = None

    @property
    def origin(self):
        if self._origin is None:
            self._origin = get_origin(self.type)
        return self._origin

    @property
    def args(self):
        if self._args is None:
            self._args = tuple(
                self._resolve_str_forward_ref(a) for a in get_args(self.type)
            )
        return self._args


if IS_GE_PYTHON38:
    from typing import get_origin, get_args

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


def get_constructor_type_hints(
    cls: Optional[Type],
    global_ns: Optional[dict] = None,
    local_ns: Optional[dict] = None,
) -> Optional[Mapping[str, Type]]:
    return typing.get_type_hints(
        cls.__init__, global_ns, local_ns
    ) or typing.get_type_hints(cls, global_ns, local_ns)


def _get_constructor_type_hints(cls: Optional[Type], common: CommonParams):
    if cls is None:
        return None
    return get_constructor_type_hints(cls, common.global_ns, common.local_ns)


def resolve_str_forward_ref(
    type_or_name: Union[str, Type],
    cls: Type,
    global_ns: Optional[dict] = None,
    local_ns: Optional[dict] = None,
) -> Type:
    """starting in Python 3.9 types can be list['class-forward-reference'].
    The inner string is not resolved like when typing.List['class-forward-reference'] is used.
    This helper will attempt to resolve these string forward references.
    """
    if isinstance(type_or_name, str):
        if local_ns and type_or_name in local_ns:
            return local_ns[type_or_name]
        elif global_ns and type_or_name in global_ns:
            return global_ns[type_or_name]
        elif hasattr(sys.modules[cls.__module__], type_or_name):
            return getattr(sys.modules[cls.__module__], type_or_name)
        else:
            raise TypeError(f"Type hint '{type_or_name}' could not be resolved")
    return type_or_name


def _from_dict(cls: Type[C], fd_from: dict, common: CommonParams):
    return from_dict(
        cls,
        fd_from,
        common.check_types,
        True,
        common.global_ns,
        common.local_ns,
    )


def from_dict(
    cls: Type[C],
    fd_from: Optional[dict] = None,
    fd_check_types: bool = False,
    fd_copy_unknown: bool = True,
    fd_global_ns: Optional[dict] = None,
    fd_local_ns: Optional[dict] = None,
    **overwrite_kwargs: Optional[dict],
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

    cls_constructor_argument_types = get_constructor_type_hints(
        cls, fd_global_ns, fd_local_ns
    )
    if not cls_constructor_argument_types:
        raise TypeError(f"Given class {cls} is not supported by from_dict")

    given_args = {}
    if fd_from:
        if not isinstance(fd_from, dict):
            raise TypeError(f"fd_from must be dict but was found to be {type(fd_from)}")
        given_args.update(fd_from)
    if overwrite_kwargs:
        given_args.update(overwrite_kwargs)

    common_params = CommonParams(fd_check_types, fd_global_ns, fd_local_ns)
    ckwargs = {}
    for cls_argument_name, cls_argument_type in cls_constructor_argument_types.items():
        if cls_argument_name == "return" and cls_argument_type is None:
            # Ignore return argument
            continue

        try:
            given_argument = given_args[cls_argument_name]
        except KeyError:
            continue

        arg_state = ArgumentState(
            cls_argument_name, cls_argument_type, given_argument, cls, common_params
        )
        try:
            # Recursively from_dict attributes which are structures, too
            if isinstance(given_argument, dict):
                argument_value = handle_dict_argument(common_params, arg_state)
            elif (
                isinstance(given_argument, list)
                and arg_state.origin
                in (list, typing.List)  # in Python36, origin is List not list
                and _get_constructor_type_hints(arg_state.args[0], common_params)
            ):
                list_var_type = arg_state.args[0]
                argument_value = [
                    _from_dict(list_var_type, x, common_params) for x in given_argument
                ]
            else:
                argument_value = given_argument
        except FromDictTypeError as e:
            # Add location for better error message
            raise FromDictTypeError(
                [cls_argument_name] + e.location, e.expected_type, e.found_type
            )

        if fd_check_types:
            try:
                type_check(argument_value, cls_argument_type)
            except FromDictTypeError as e:
                # Add location for better error message
                raise FromDictTypeError(
                    [cls_argument_name] + e.location, e.expected_type, e.found_type
                )

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


def handle_dict_argument(
    common_params: CommonParams, arg_state: ArgumentState
) -> object:
    if arg_state.origin == dict:
        if _get_constructor_type_hints(arg_state.args[1], common_params):
            # Dict[a,b]; we only support b being a structure.
            key_type, value_type = arg_state.args
            if common_params.check_types:  # Perform type check on keys
                all(type_check(k, key_type) for k in arg_state.value.keys())
            argument_value = {
                k: _from_dict(value_type, v, common_params)
                for k, v in arg_state.value.items()
            }
        else:
            # The dictionary contains values that are primitives (int, str)
            argument_value = arg_state.value
    elif arg_state.origin == Union:
        if (
            len(arg_state.args) == 2
            and arg_state.args[1] == type(None)  # Optional
            and _get_constructor_type_hints(arg_state.args[0], common_params)
        ):
            argument_value = _from_dict(
                arg_state.args[0], arg_state.value, common_params
            )
        else:
            argument_value = arg_state.value
            for arg_type in arg_state.args:
                if arg_type == type(None):
                    continue
                required_keys = {
                    k for k in _get_constructor_type_hints(arg_type, common_params)
                }
                required_keys.discard("return")
                if all(k in required_keys for k in arg_state.value):
                    try:
                        argument_value = _from_dict(
                            arg_type, arg_state.value, common_params
                        )
                        break
                    except TypeError:
                        pass
    elif _get_constructor_type_hints(arg_state.type, common_params):
        argument_value = _from_dict(arg_state.type, arg_state.value, common_params)
    else:
        argument_value = arg_state.value
    return argument_value
