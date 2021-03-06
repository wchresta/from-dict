from typing import Optional, List, Type, NamedTuple, Union, Dict

import attr
import pytest
import sys

from from_dict import from_dict, FromDictTypeError

if sys.version_info[:2] >= (3, 7):
    from dataclasses import dataclass
else:
    from attr import dataclass


@dataclass
class Structures:
    outer_structure: Type
    inner_structure: Type
    does_type_validation: bool
    has_dict: bool


# Attr style structures
@attr.s(auto_attribs=True)
class SubTestDictAttr:
    foo: int
    bar: str


@attr.s(auto_attribs=True)
class MainTestDictAttr:
    foo: int
    baz: SubTestDictAttr


@attr.s(auto_attribs=True)
class SubTestDictAttrWithValidators:
    foo: int = attr.ib(validator=attr.validators.instance_of(int))
    bar: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True)
class MainTestDictAttrWithValidators:
    foo: int = attr.ib(validator=attr.validators.instance_of(int))
    baz: SubTestDictAttrWithValidators = attr.ib(validator=attr.validators.instance_of(SubTestDictAttrWithValidators))


# Dataclass structures
@dataclass(frozen=True)
class SubTestDictDataclass:
    foo: int
    bar: str


@dataclass(frozen=True)
class MainTestDictDataclass:
    foo: int
    baz: SubTestDictDataclass


# NamedTuple structures
class SubTestDictNamedTuple(NamedTuple):
    foo: int
    bar: str


class MainTestDictNamedTuple(NamedTuple):
    foo: int
    baz: SubTestDictNamedTuple


@pytest.fixture(params=[
    pytest.param(Structures(MainTestDictAttr, SubTestDictAttr, False, True), id="attr"),
    pytest.param(Structures(MainTestDictAttr, SubTestDictAttr, True, True), id="attr-with-validators"),
    pytest.param(Structures(MainTestDictDataclass, SubTestDictDataclass, False, True), id="dataclass"),
    pytest.param(Structures(MainTestDictNamedTuple, SubTestDictNamedTuple, False, False), id="named-tuple"),
])
def structures(request):
    yield request.param


def test_packing(structures):
    input_dict = {
        "foo": 22,
        "baz": {
            "foo": 42,
            "bar": "Works :)",
        }
    }

    main_object = from_dict(structures.outer_structure, input_dict)

    assert main_object.baz.bar == "Works :)"
    assert isinstance(main_object, structures.outer_structure)
    assert isinstance(main_object.baz, structures.inner_structure)


def test_keyword_style(structures):
    m = from_dict(structures.outer_structure, foo=22, baz=structures.inner_structure(foo=42, bar="Works :)"))
    assert m.foo == 22
    assert m.baz.foo == 42
    assert m.baz.bar == "Works :)"


def test_keyword_style_overwrites_positional(structures):
    assert from_dict(structures.inner_structure, {"foo": 42, "bar": "Works :)"}, foo=0).foo == 0


def test_additional_keys_are_allowed(structures):
    my_obj = from_dict(structures.inner_structure, foo=22, bar="Works", additional=[1, 2, 3])
    assert my_obj.foo == 22
    assert my_obj.bar == "Works"

    if structures.has_dict:
        assert my_obj.additional == [1, 2, 3]


def test_missing_key(structures):
    with pytest.raises(TypeError):
        from_dict(structures.inner_structure, {"foo": 22})


def test_invalid_type_inherent(structures):
    if not structures.does_type_validation:
        pytest.skip("Structure does not support inherent runtime type checking")

    with pytest.raises(TypeError) as e:
        from_dict(structures.inner_structure, {"foo": "wrong", "bar": "right"}, fd_check_types=True)


def test_invalid_type_from_dict(structures):
    with pytest.raises(FromDictTypeError) as e:
        from_dict(structures.inner_structure, {"foo": "wrong", "bar": "right"}, fd_check_types=True)

    assert str(e.value) == "For \"foo\", expected <class 'int'> but found <class 'str'>"


def test_missing_key_discovered_in_subdict_inherent(structures):
    if not structures.does_type_validation:
        pytest.skip("Structure does not support inherent runtime type checking")

    with pytest.raises(TypeError):
        from_dict(structures.outer_structure, {"foo": 22, "baz": {"foo": 42}})


def test_invalid_type_discovered_in_subdict_from_dict(structures):
    with pytest.raises(FromDictTypeError) as e:
        from_dict(structures.outer_structure, {"foo": 22, "baz": {"foo": 42, "bar": ["wrong type"]}},
                  fd_check_types=True)

    assert str(e.value) == "For \"baz.bar\", expected <class 'str'> but found <class 'list'>"


def test_invalid_type_discovered_in_subdict(structures):
    with pytest.raises(FromDictTypeError) as e:
        from_dict(structures.outer_structure, {"foo": 22, "baz": {"foo": 42, "bar": ["wrong type"]}},
                  fd_check_types=True)

    assert str(e.value) == "For \"baz.bar\", expected <class 'str'> but found <class 'list'>"


def test_subscripted_attr_generics_work():
    @attr.s(auto_attribs=True)
    class KDict:
        a: int
        b: Optional[str]
        c: List[int]

    opt = from_dict(KDict, a=11, b=None, c=[1, 2, 3])

    assert opt.a == 11
    assert opt.b is None
    assert opt.c == [1, 2, 3]
    assert from_dict(KDict, a=11, b="hi", c=[1, 2, 3]).b == "hi"


def test_list_of_structures_work(structures):
    @attr.s(auto_attribs=True)
    class KList:
        a: List[structures.inner_structure]

    val = {
        "a": [
            {"foo": 11, "bar": "Hi"},
            {"foo": 13, "bar": "Sup"},
            {"foo": -4, "bar": "Ya"},
        ]
    }
    structs = from_dict(KList, val, fd_check_types=not structures.does_type_validation)

    assert structs.a[0].foo == 11
    assert [el.foo for el in structs.a] == [11, 13, -4]
    assert [el.bar for el in structs.a] == ["Hi", "Sup", "Ya"]


def test_dict_with_substructure(structures):
    @attr.s(auto_attribs=True)
    class SubDict:
        a: Dict[int, structures.inner_structure]

    val = {
        "a": {
            11: {"foo": 11, "bar": "Hi"},
            13: {"foo": 13, "bar": "Sup"},
            -4: {"foo": -4, "bar": "Ya"},
        }
    }
    structs = from_dict(SubDict, val, fd_check_types=not structures.does_type_validation)
    assert all(k == v.foo for k, v in structs.a.items())


def test_union_works():
    @attr.s(auto_attribs=True)
    class UClass:
        a: Union[str, int]

    assert from_dict(UClass, {"a": "hello"}, fd_check_types=True).a == "hello"
    assert from_dict(UClass, {"a": 22}, fd_check_types=True).a == 22

    assert from_dict(UClass, {"a": "hello"}, fd_check_types=True).a == "hello"
    assert from_dict(UClass, {"a": 22}, fd_check_types=True).a == 22
