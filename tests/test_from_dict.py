from dataclasses import dataclass
from typing import Dict, List, NamedTuple, Optional, Type, Union, TypeVar, Generic

import attr
import pytest
from from_dict import FromDictTypeError, FromDictUnknownArgsError, from_dict


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


# Dataclass structures
@dataclass(frozen=True)
class MainTestDictDataclassFrwRef:
    foo: int
    baz: 'SubTestDictDataclassFrwRef'


@dataclass(frozen=True)
class SubTestDictDataclassFrwRef:
    foo: int
    bar: str

@pytest.fixture(params=[
    pytest.param(Structures(MainTestDictAttr, SubTestDictAttr, False, True), id="attr"),
    pytest.param(Structures(MainTestDictAttr, SubTestDictAttr, True, True), id="attr-with-validators"),
    pytest.param(Structures(MainTestDictDataclass, SubTestDictDataclass, False, True), id="dataclass"),
    pytest.param(Structures(MainTestDictDataclassFrwRef, SubTestDictDataclassFrwRef, False, True), id="dataclass-forward-ref"),
    pytest.param(Structures(MainTestDictNamedTuple, SubTestDictNamedTuple, False, False), id="named-tuple"),
])
def structures(request):
    yield request.param


def test_packing(structures: Structures):
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


def test_keyword_style(structures: Structures):
    m = from_dict(structures.outer_structure, foo=22, baz=structures.inner_structure(foo=42, bar="Works :)"))
    assert m.foo == 22
    assert m.baz.foo == 42
    assert m.baz.bar == "Works :)"


def test_keyword_style_overwrites_positional(structures: Structures):
    assert from_dict(structures.inner_structure, {"foo": 42, "bar": "Works :)"}, foo=0).foo == 0


def test_additional_keys_are_allowed(structures: Structures):
    my_obj = from_dict(structures.inner_structure, foo=22, bar="Works", additional=[1, 2, 3])
    assert my_obj.foo == 22
    assert my_obj.bar == "Works"

    if structures.has_dict:
        assert my_obj.additional == [1, 2, 3]


def test_missing_key(structures: Structures):
    with pytest.raises(TypeError):
        from_dict(structures.inner_structure, {"foo": 22})


def test_invalid_type_inherent(structures: Structures):
    if not structures.does_type_validation:
        pytest.skip("Structure does not support inherent runtime type checking")

    with pytest.raises(TypeError) as e:
        from_dict(structures.inner_structure, {"foo": "wrong", "bar": "right"}, fd_check_types=True)


def test_invalid_type_from_dict(structures: Structures):
    with pytest.raises(FromDictTypeError) as e:
        from_dict(structures.inner_structure, {"foo": "wrong", "bar": "right"}, fd_check_types=True)

    assert str(e.value) == "For \"foo\", expected <class 'int'> but found <class 'str'>"


def test_missing_key_discovered_in_subdict_inherent(structures: Structures):
    if not structures.does_type_validation:
        pytest.skip("Structure does not support inherent runtime type checking")

    with pytest.raises(TypeError):
        from_dict(structures.outer_structure, {"foo": 22, "baz": {"foo": 42}})


def test_invalid_type_discovered_in_subdict_from_dict(structures: Structures):
    with pytest.raises(FromDictTypeError) as e:
        from_dict(structures.outer_structure, {"foo": 22, "baz": {"foo": 42, "bar": ["wrong type"]}},
                  fd_check_types=True)

    assert str(e.value) == "For \"baz.bar\", expected <class 'str'> but found <class 'list'>"


def test_invalid_type_discovered_in_subdict(structures: Structures):
    with pytest.raises(FromDictTypeError) as e:
        from_dict(structures.outer_structure, {"foo": 22, "baz": {"foo": 42, "bar": ["wrong type"]}},
                  fd_check_types=True)

    assert str(e.value) == "For \"baz.bar\", expected <class 'str'> but found <class 'list'>"


def test_invalid_list_element_type():
    @dataclass(frozen=True)
    class TstClass:
        a: int
        b: Optional[str]
        c: List[int]
        d: Dict[str, int]

    with pytest.raises(FromDictTypeError) as e:
        opt = from_dict(TstClass, a=11, b=None, c=[1, 2, 3, "bad"], d={"a":1, "b": 2}, fd_check_types=True)

    assert str(e.value) == "For \"c[3]\", expected <class 'int'> but found <class 'str'>"
    assert not e.value.__suppress_context__


def test_invalid_dict_element_type():
    @dataclass(frozen=True)
    class TstClass:
        a: int
        b: Optional[str]
        c: List[int]
        d: Dict[str, int]

    with pytest.raises(FromDictTypeError) as e:
        opt = from_dict(TstClass, a=11, b=None, c=[1, 2, 3, 4], d={"a":1, "b": 2, "C": "bad"}, fd_check_types=True)

    assert str(e.value) == "For \"d['C']\", expected <class 'int'> but found <class 'str'>"
    assert not e.value.__suppress_context__


def test_invalid_list_element_type_in_subclass():
    @dataclass(frozen=True)
    class TstClass:
        a: int
        b: Optional[str]
        c: List[int]
        d: Dict[str, int]

    @dataclass(frozen=True)
    class TstClassMain:
        foo: TstClass

    with pytest.raises(FromDictTypeError) as e:
        opt = from_dict(TstClassMain, foo=dict(a=11, b=None, c=[1, 2, 3, "bad"], d={"a":1, "b": 2}), fd_check_types=True)

    assert str(e.value) == "For \"foo.c[3]\", expected <class 'int'> but found <class 'str'>"
    assert e.value.__suppress_context__


def test_invalid_dict_element_type_in_subclass():
    @dataclass(frozen=True)
    class TstClass:
        a: int
        b: Optional[str]
        c: List[int]
        d: Dict[str, int]

    @dataclass(frozen=True)
    class TstClassMain:
        foo: TstClass

    with pytest.raises(FromDictTypeError) as e:
        opt = from_dict(TstClassMain, foo=dict(a=11, b=None, c=[1, 2, 3, 4], d={"a":1, "b": 2, "C": "bad"}), fd_check_types=True)

    assert str(e.value) == "For \"foo.d['C']\", expected <class 'int'> but found <class 'str'>"
    assert e.value.__suppress_context__


def test_subscripted_attr_generics_work():
    @attr.s(auto_attribs=True)
    class KDict:
        a: int
        b: Optional[str]
        c: List[int]
        d: Dict[str, int]

    opt = from_dict(KDict, a=11, b=None, c=[1, 2, 3], d={"a":1, "b": 2})

    assert opt.a == 11
    assert opt.b is None
    assert opt.c == [1, 2, 3]
    assert opt.d == {"a":1, "b": 2}
    assert from_dict(KDict, a=11, b="hi", c=[1, 2, 3], d={"a":1, "b": 2}).b == "hi"


def test_dataclass_generics_work():
    @dataclass(frozen=True)
    class KDict:
        a: int
        b: Optional[str]
        c: List[int]
        d: Dict[str, int]

    opt = from_dict(KDict, a=11, b=None, c=[1, 2, 3], d={"a":1, "b": 2})

    assert opt.a == 11
    assert opt.b is None
    assert opt.c == [1, 2, 3]
    assert opt.d == {"a":1, "b": 2}

    opt = from_dict(KDict, dict(a=11, b="hi", c=[1, 2, 3], d={"a":1, "b": 2}))

    assert opt.a == 11
    assert opt.b == "hi"
    assert opt.c == [1, 2, 3]
    assert opt.d == {"a":1, "b": 2}


def test_list_of_structures_work(structures: Structures):
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


def test_dict_with_substructure(structures: Structures):
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


def test_generic_dataclass():
    TField1 = TypeVar('TField1')
    TField2 = TypeVar('TField2')
    @dataclass(frozen=True)
    class Data1:
        value: int

    @dataclass(frozen=True)
    class Data2:
        value: str

    @dataclass(frozen=True)
    class TstClassMain(Generic[TField1, TField2]):
        field_1: TField1
        field_2: TField2
        field_3: str
        field_4: int

    v = from_dict(TstClassMain[Data1, Data2], field_1=dict(value=1), field_2={"value":"1"}, field_3="s", field_4=1, fd_check_types=True)
    assert isinstance(v.field_1, Data1)
    assert isinstance(v.field_2, Data2)
    assert isinstance(v.field_3, str)
    assert isinstance(v.field_4, int)

    v = from_dict(TstClassMain[Data2, Data1], field_1=dict(value="1"), field_2={"value":1}, field_3="s", field_4=1, fd_check_types=True)
    assert isinstance(v.field_1, Data2)
    assert isinstance(v.field_2, Data1)
    assert isinstance(v.field_3, str)
    assert isinstance(v.field_4, int)


def test_parent_generic_dataclass():
    TField1 = TypeVar('TField1')
    TField2 = TypeVar('TField2')
    @dataclass(frozen=True)
    class Data1:
        value: int

    @dataclass(frozen=True)
    class Data2:
        value: str

    @dataclass(frozen=True)
    class TstClassMainParent(Generic[TField1, TField2]):
        field_1: TField1
        field_2: TField2
        field_3: str
        field_4: int

    @dataclass(frozen=True)
    class TstClassMain(TstClassMainParent[Data1, Data2]):
        pass

    v = from_dict(TstClassMain, field_1=dict(value=1), field_2={"value":"1"}, field_3="s", field_4=1, fd_check_types=True)
    assert isinstance(v.field_1, Data1)
    assert isinstance(v.field_2, Data2)
    assert isinstance(v.field_3, str)
    assert isinstance(v.field_4, int)


def test_generic_norm_class():
    TParam1 = TypeVar('TParam1')
    TParam2 = TypeVar('TParam2')
    @dataclass(frozen=True)
    class Data1:
        value: int

    @dataclass(frozen=True)
    class Data2:
        value: str

    class TstClassMain(Generic[TParam1, TParam2]):
        def __init__(self, param_1: TParam1, param_2: TParam2, param_3: str, param_4: int) -> None:
            self.field_1 = param_1
            self.field_2 = param_2
            self.field_3 = param_3
            self.field_4 = param_4

    v = from_dict(TstClassMain[Data1, Data2], param_1={"value":1}, param_2=dict(value="1"), param_3="s", param_4=1, fd_check_types=True)
    assert isinstance(v.field_1, Data1)
    assert isinstance(v.field_2, Data2)
    assert isinstance(v.field_3, str)
    assert isinstance(v.field_4, int)

    v = from_dict(TstClassMain[Data2, Data1], param_1={"value":"1"}, param_2=dict(value=1), param_3="s", param_4=1, fd_check_types=True)
    assert isinstance(v.field_1, Data2)
    assert isinstance(v.field_2, Data1)
    assert isinstance(v.field_3, str)
    assert isinstance(v.field_4, int)


def test_parent_generic_norm_class():
    TParam1 = TypeVar('TParam1')
    TParam2 = TypeVar('TParam2')
    @dataclass(frozen=True)
    class Data1:
        value: int

    @dataclass(frozen=True)
    class Data2:
        value: str

    class TstClassMainParent(Generic[TParam1, TParam2]):
        def __init__(self, param_1: TParam1, param_2: TParam2, param_3: str, param_4: int) -> None:
            self.field_1 = param_1
            self.field_2 = param_2
            self.field_3 = param_3
            self.field_4 = param_4

    class TstClassMain(TstClassMainParent[Data1, Data2]):
        pass

    v = from_dict(TstClassMain, param_1={"value":1}, param_2=dict(value="1"), param_3="s", param_4=1, fd_check_types=True)
    assert isinstance(v.field_1, Data1)
    assert isinstance(v.field_2, Data2)
    assert isinstance(v.field_3, str)
    assert isinstance(v.field_4, int)


def test_generic_dataclass_with_generic_fields():
    TField1 = TypeVar('TField1')
    TField2 = TypeVar('TField2')
    @dataclass(frozen=True)
    class Data1:
        value: int

    @dataclass(frozen=True)
    class Data2:
        value: str

    @dataclass(frozen=True)
    class TstClassMain(Generic[TField1, TField2]):
        f_1: Optional[TField1]
        f_2: List[TField2]

    v = from_dict(TstClassMain[Data1, Data2], {"f_1": {"value":1}, "f_2": [{"value":"1"}] }, fd_check_types=True)
    assert isinstance(v.f_1, Data1)
    assert isinstance(v.f_2, list)
    assert isinstance(v.f_2[0], Data2)

    v = from_dict(TstClassMain[Data1, Data2], {"f_1": None, "f_2": [{"value":"1"}] }, fd_check_types=True)
    assert v.f_1 is None
    assert isinstance(v.f_2, list)
    assert isinstance(v.f_2[0], Data2)

    v = from_dict(TstClassMain[Data2, Data1], {"f_1": {"value":"1"}, "f_2": [{"value":1}]}, fd_check_types=True)
    assert isinstance(v.f_1, Data2)
    assert isinstance(v.f_2, list)
    assert isinstance(v.f_2[0], Data1)

    v = from_dict(TstClassMain['Data2', 'Data1'], {"f_1": {"value":"1"}, "f_2": [{"value":1}]}, fd_local_ns=locals(), fd_check_types=True)
    assert isinstance(v.f_1, Data2)
    assert isinstance(v.f_2, list)
    assert isinstance(v.f_2[0], Data1)


def test_parent_generic_dataclass_with_generic_fields():
    TField1 = TypeVar('TField1')
    TField2 = TypeVar('TField2')
    @dataclass(frozen=True)
    class Data1:
        value: int

    @dataclass(frozen=True)
    class Data2:
        value: str

    @dataclass(frozen=True)
    class TstClassMainParent(Generic[TField1, TField2]):
        f_1: Optional[TField1]
        f_2: List[TField2]

    class TstClassMain(TstClassMainParent[Data1, Data2]):
        pass

    v = from_dict(TstClassMain, {"f_1": {"value":1}, "f_2": [{"value":"1"}] }, fd_check_types=True)
    assert isinstance(v.f_1, Data1)
    assert isinstance(v.f_2, list)
    assert isinstance(v.f_2[0], Data2)

    v = from_dict(TstClassMain, {"f_1": None, "f_2": [{"value":"1"}] }, fd_check_types=True)
    assert v.f_1 is None
    assert isinstance(v.f_2, list)
    assert isinstance(v.f_2[0], Data2)

def test_error_on_unknown_args():
    # Verify these don't raise an error
    from_dict(SubTestDictDataclass, foo=1, bar="s", fd_check_types=True)
    from_dict(SubTestDictDataclass, foo=1, bar="s", fd_check_types=True, fd_error_on_unknown=True, fd_copy_unknown=False)
    from_dict(SubTestDictDataclass, foo=1, bar="s", sam=1, fd_check_types=True)

    with pytest.raises(FromDictUnknownArgsError) as e:
        from_dict(SubTestDictDataclass, foo=1, bar="s", sam=1, fd_error_on_unknown=True, fd_copy_unknown=False, fd_check_types=True)
    
    # Verify these don't raise an error
    from_dict(MainTestDictDataclass, foo=1, baz=dict(foo=1, bar="s"), fd_check_types=True)
    from_dict(MainTestDictDataclass, foo=1, baz=dict(foo=1, bar="s"), fd_check_types=True, fd_error_on_unknown=True, fd_copy_unknown=False)
    from_dict(MainTestDictDataclass, foo=1, baz=dict(foo=5, bar="s", sam=2), fd_check_types=True)

    with pytest.raises(FromDictUnknownArgsError) as e:
        from_dict(MainTestDictDataclass, foo=1, baz=dict(foo=5, bar="s", sam=2), fd_error_on_unknown=True, fd_copy_unknown=False, fd_check_types=True)
    
    @dataclass
    class ClassWithDefaults:
        foo: int = 1
        bar: str = "default"
          
    # Verify these don't raise an error
    from_dict(ClassWithDefaults, foo=3, fd_check_types=True)
    from_dict(ClassWithDefaults, fd_check_types=True, fd_error_on_unknown=True, fd_copy_unknown=False)
    from_dict(ClassWithDefaults, sam=1, fd_check_types=True)

    with pytest.raises(FromDictUnknownArgsError) as e:
        from_dict(ClassWithDefaults, sam=1, fd_error_on_unknown=True, fd_copy_unknown=False, fd_check_types=True)