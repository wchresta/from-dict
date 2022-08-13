import copy
import datetime
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Type, Callable

from from_dict import FromDictTypeError, from_dict

import attr
import pytest

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# Classes used by the tests

class NormalClass:
    def __init__(self, v: str) -> None:
        self.value = v

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NormalClass) and self.value == other.value


@dataclass(frozen=True)
class DataClass:
    field: str


@attr.s(auto_attribs=True)
class AttrClass:
    attrib: str


@dataclass
class ClassPrimitives:
    normal: int
    optional: Optional[int]
    union: Union[int, str, NormalClass, DataClass]
    any: Any
    self_ref: Optional['ClassPrimitives']

    list_normal: List[int]
    list_optional: List[Optional[int]]
    list_union: List[Union[int, str, NormalClass, DataClass]]
    list_any: List[Any]
    list_self_ref: List['ClassPrimitives']
    
    dict_normal: Dict[str, int]
    dict_optional: Dict[str, Optional[int]]
    dict_union: Dict[str, Union[int, str, NormalClass, DataClass]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassPrimitives']


@dataclass
class ClassDict:
    normal: Dict[str,str]
    optional: Optional[Dict[str,str]]
    union: Union[str, NormalClass, DataClass, Dict[str,str]]
    any: Any
    self_ref: Optional['ClassDict']

    list_normal: List[Dict[str,str]]
    list_optional: List[Optional[Dict[str,str]]]
    list_union: List[Union[str, NormalClass, DataClass, Dict[str,str]]]
    list_any: List[Any]
    list_self_ref: List['ClassDict']
    
    dict_normal: Dict[str, Dict[str,str]]
    dict_optional: Dict[str, Optional[Dict[str,str]]]
    dict_union: Dict[str, Union[str, NormalClass, DataClass, Dict[str,str]]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassDict']


@dataclass
class ClassDictSimple:
    normal: Dict[str,str]
    optional: Optional[dict]
    union: Union[str, NormalClass, DataClass, dict]
    any: Any
    self_ref: Optional['ClassDictSimple']

    list_normal: List[dict]
    list_optional: List[Optional[dict]]
    list_union: List[Union[str, NormalClass, DataClass, dict]]
    list_any: List[Any]
    list_self_ref: List['ClassDictSimple']
    
    dict_normal: Dict[str, dict]
    dict_optional: Dict[str, Optional[dict]]
    dict_union: Dict[str, Union[str, NormalClass, DataClass, dict]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassDictSimple']


@dataclass
class ClassList:
    normal: List[str]
    optional: Optional[List[str]]
    union: Union[str, NormalClass, DataClass, List[str]]
    any: Any
    self_ref: Optional['ClassList']

    list_normal: List[List[str]]
    list_optional: List[Optional[List[str]]]
    list_union: List[Union[str, NormalClass, DataClass, List[str]]]
    list_any: List[Any]
    list_self_ref: List['ClassList']
    
    dict_normal: Dict[str, List[str]]
    dict_optional: Dict[str, Optional[List[str]]]
    dict_union: Dict[str, Union[str, NormalClass, DataClass, List[str]]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassList']


@dataclass
class ClassDataClass:
    normal: DataClass
    optional: Optional[DataClass]
    union: Union[DataClass, str, NormalClass, DataClass]
    any: Any
    self_ref: Optional['ClassDataClass']

    list_normal: List[DataClass]
    list_optional: List[Optional[DataClass]]
    list_union: List[Union[DataClass, str, NormalClass, DataClass]]
    list_any: List[Any]
    list_self_ref: List['ClassDataClass']
    
    dict_normal: Dict[str, DataClass]
    dict_optional: Dict[str, Optional[DataClass]]
    dict_union: Dict[str, Union[DataClass, str, NormalClass, DataClass]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassDataClass']


@dataclass
class ClassNormalClass:
    normal: NormalClass
    optional: Optional[NormalClass]
    union: Union[NormalClass, str, NormalClass, DataClass]
    any: Any
    self_ref: Optional['ClassNormalClass']

    list_normal: List[NormalClass]
    list_optional: List[Optional[NormalClass]]
    list_union: List[Union[NormalClass, str, NormalClass, DataClass]]
    list_any: List[Any]
    list_self_ref: List['ClassNormalClass']
    
    dict_normal: Dict[str, NormalClass]
    dict_optional: Dict[str, Optional[NormalClass]]
    dict_union: Dict[str, Union[NormalClass, str, NormalClass, DataClass]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassNormalClass']


@dataclass
class ClassAttrClass:
    normal: AttrClass
    optional: Optional[AttrClass]
    union: Union[AttrClass, str, NormalClass, DataClass]
    any: Any
    self_ref: Optional['ClassAttrClass']

    list_normal: List[AttrClass]
    list_optional: List[Optional[AttrClass]]
    list_union: List[Union[AttrClass, str, NormalClass, DataClass]]
    list_any: List[Any]
    list_self_ref: List['ClassAttrClass']
    
    dict_normal: Dict[str, AttrClass]
    dict_optional: Dict[str, Optional[AttrClass]]
    dict_union: Dict[str, Union[AttrClass, str, NormalClass, DataClass]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassAttrClass']


@dataclass
class ClassListDataClass:
    normal: List[DataClass]
    optional: Optional[List[DataClass]]
    union: Union[str, NormalClass, DataClass, List[DataClass]]
    any: Any
    self_ref: Optional['ClassListDataClass']

    list_normal: List[List[DataClass]]
    list_optional: List[Optional[List[DataClass]]]
    list_union: List[Union[str, NormalClass, DataClass, List[DataClass]]]
    list_any: List[Any]
    list_self_ref: List['ClassListDataClass']
    
    dict_normal: Dict[str, List[DataClass]]
    dict_optional: Dict[str, Optional[List[DataClass]]]
    dict_union: Dict[str, Union[str, NormalClass, DataClass, List[DataClass]]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassListDataClass']


@dataclass
class ClassDictDataClass:
    normal: Dict[str, DataClass]
    optional: Optional[Dict[str, DataClass]]
    union: Union[str, NormalClass, DataClass, Dict[str, DataClass]]
    any: Any
    self_ref: Optional['ClassDictDataClass']

    list_normal: List[Dict[str, DataClass]]
    list_optional: List[Optional[Dict[str, DataClass]]]
    list_union: List[Union[str, NormalClass, DataClass, Dict[str, DataClass]]]
    list_any: List[Any]
    list_self_ref: List['ClassDictDataClass']
    
    dict_normal: Dict[str, Dict[str, DataClass]]
    dict_optional: Dict[str, Optional[Dict[str, DataClass]]]
    dict_union: Dict[str, Union[str, NormalClass, DataClass, Dict[str, DataClass]]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, 'ClassDictDataClass']

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# helper functions

def initialize(cls, init_func, any_init = None):
        any_init = any_init or init_func
        return cls(
        normal = init_func(),
        optional = init_func(),
        union = init_func(),
        any = any_init(), # If this is a dict, it will not be converted to a dataclass
        self_ref = None,

        list_normal = [init_func()],
        list_optional = [None, init_func()],
        list_union = ["first", init_func()],
        list_any = [datetime.datetime.now().date(), {"v": "VALUE"}, {"field": "ANY"}],
        list_self_ref = [],

        dict_normal = {"k": init_func()},
        dict_optional = {"K1": None, "K2":init_func()},
        dict_union = {"k1": "first", "k2":init_func()},
        dict_any = {"k1":datetime.datetime.now().date(), "k2":{"v": "VALUE"}, "k3":{"field": "ANY"}},
        dict_self_ref = {},
    )


@contextmanager
def expect_type_error():
    try:
        yield None
    except FromDictTypeError:
        return
    raise AssertionError("Expected 'FromDictTypeError' to be raised")


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# PyTest framework
@dataclass
class NormTestParams:
    cls: Type
    dic_init_func: Callable
    expected_init_func: Callable


@pytest.fixture(params=[
    pytest.param(NormTestParams(ClassPrimitives, lambda: 4, lambda: 4), id="primitives"),
    pytest.param(NormTestParams(ClassDict, lambda: {"d":"Vvv"}, lambda: {"d":"Vvv"}), id="dict"),
    pytest.param(NormTestParams(ClassDictSimple, lambda: {"d":"Vvv"}, lambda: {"d":"Vvv"}), id="dict-2"),
    pytest.param(NormTestParams(ClassList, lambda: ["1", "2"], lambda: ["1", "2"]), id="list"),
    
    pytest.param(NormTestParams(ClassDataClass, lambda: {"field": "value"}, lambda: DataClass("value")), id="data-class"),
    pytest.param(NormTestParams(ClassNormalClass, lambda: {"v": "value"}, lambda: NormalClass("value")), id="norm-class"),
    pytest.param(NormTestParams(ClassAttrClass, lambda: {"attrib": "value"}, lambda: AttrClass("value")), id="attr-class"),

    pytest.param(NormTestParams(ClassListDataClass, lambda: [{"field": "value"}], lambda: [DataClass("value")]), id="list-data-class"),
    pytest.param(NormTestParams(ClassDictDataClass, lambda: {"KEY":{"field": "value"}}, lambda: {"KEY":DataClass("value")}), id="dict-data-class"),
])
def norm_params(request):
    yield request.param

@dataclass
class NegativeTestParams:
    cls: Type
    dic_init_func: Callable
    bad_init_func: Callable


@pytest.fixture(params=[
    pytest.param(NegativeTestParams(ClassPrimitives, lambda: 4, datetime.datetime.now), id="primitives"),
    pytest.param(NegativeTestParams(ClassDict, lambda: {"d":"Vvv"}, datetime.datetime.now), id="dict"),
    pytest.param(NegativeTestParams(ClassDictSimple, lambda: {"d":"Vvv"}, datetime.datetime.now), id="dict-2"),
    pytest.param(NegativeTestParams(ClassList, lambda: ["1", "2"], datetime.datetime.now), id="list"),

    pytest.param(NegativeTestParams(ClassDataClass, lambda: {"field": "value"}, datetime.datetime.now), id="data-class"),
    pytest.param(NegativeTestParams(ClassNormalClass, lambda: {"v": "value"}, datetime.datetime.now), id="norm-class"),
    pytest.param(NegativeTestParams(ClassAttrClass, lambda: {"attrib": "value"}, datetime.datetime.now), id="attr-class"),
    
    pytest.param(NegativeTestParams(ClassListDataClass, lambda: [{"field": "value"}], datetime.datetime.now), id="list-data-class"),
    pytest.param(NegativeTestParams(ClassDictDataClass, lambda: {"KEY":{"field": "value"}}, datetime.datetime.now), id="dict-data-class"),
])
def negative_params(request):
    yield request.param

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# The tests

def test_basic(norm_params: NormTestParams):
    data_1 = initialize(dict, norm_params.dic_init_func)
    obj_1 = from_dict(norm_params.cls, data_1, fd_check_types=True)
    
    expected_1 = initialize(norm_params.cls, norm_params.expected_init_func, norm_params.dic_init_func)
    assert obj_1 == expected_1


def test_self_ref(norm_params: NormTestParams):
    data_1 = initialize(dict, norm_params.dic_init_func)
    obj_1 = from_dict(norm_params.cls, data_1, fd_check_types=True)
    
    expected_1 = initialize(norm_params.cls, norm_params.expected_init_func, norm_params.dic_init_func)
    assert obj_1 == expected_1
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data_2 = copy.deepcopy(data_1)
    expected_2 = copy.deepcopy(expected_1)
    data_2['self_ref'] = data_1
    expected_2.self_ref = expected_1

    obj_2 = from_dict(norm_params.cls, data_2, fd_check_types=True)
    assert obj_2 == expected_2
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data_3 = copy.deepcopy(data_2)
    expected_3 = copy.deepcopy(expected_2)
    data_3['list_self_ref'] = [data_1]
    expected_3.list_self_ref = [expected_1]

    obj_3 = from_dict(norm_params.cls, data_3, fd_check_types=True)
    assert obj_3 == expected_3
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data_4 = copy.deepcopy(data_3)
    expected_4 = copy.deepcopy(expected_3)
    data_4['dict_self_ref'] = {"k1":data_1, "k2":data_2}
    expected_4.dict_self_ref = {"k1":expected_1, "k2":expected_2}

    obj_4 = from_dict(norm_params.cls, data_4, fd_check_types=True)
    assert obj_4 == expected_4


def test_union(norm_params: NormTestParams):
    data = initialize(dict, norm_params.dic_init_func)
    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    
    expected = initialize(norm_params.cls, norm_params.expected_init_func, norm_params.dic_init_func)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['union'] = "str"
    expected.union = "str"

    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['union'] = NormalClass("val")
    expected.union = NormalClass("val")

    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['union'] = {"v": "val"}
    expected.union = NormalClass("val")
    
    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['union'] = DataClass("FIELD")
    expected.union = DataClass("FIELD")

    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['union'] = {"field": "FIELD"}
    expected.union = DataClass("FIELD")
    
    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected


def test_list_union(norm_params: NormTestParams):
    data = initialize(dict, norm_params.dic_init_func)
    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    
    expected = initialize(norm_params.cls, norm_params.expected_init_func, norm_params.dic_init_func)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'].append("str")
    expected.list_union.append("str")

    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'].append(NormalClass("val"))
    expected.list_union.append(NormalClass("val"))

    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'].append({"v": "val"})
    expected.list_union.append(NormalClass("val"))
    
    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'].append(DataClass("FIELD"))
    expected.list_union.append(DataClass("FIELD"))

    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'].append({"field": "FIELD"})
    expected.list_union.append(DataClass("FIELD"))
    
    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'] = [NormalClass("val")]
    expected.list_union = [NormalClass("val")]

    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'] = [{"v": "val"}]
    expected.list_union = [NormalClass("val")]
    
    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'] = [DataClass("FIELD")]
    expected.list_union = [DataClass("FIELD")]

    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data['list_union'] = [{"field": "FIELD"}]
    expected.list_union = [DataClass("FIELD")]
    
    obj = from_dict(norm_params.cls, data, fd_check_types=True)
    assert obj == expected


def verify_negative_basic(negative_params: NegativeTestParams):
    data = initialize(dict, negative_params.dic_init_func)
    data["normal"] = negative_params.bad_init_func()

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["optional"] = negative_params.bad_init_func()

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["union"] = negative_params.bad_init_func()

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["self_ref"] = negative_params.bad_init_func()

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    

def test_negative_list(negative_params: NegativeTestParams):
    data = initialize(dict, negative_params.dic_init_func)
    data["list_normal"] = [negative_params.bad_init_func()]

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["list_optional"] = [negative_params.bad_init_func()]

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["list_union"] = [negative_params.bad_init_func()]

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["list_self_ref"] = [negative_params.bad_init_func()]

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)


def test_negative_dict(negative_params: NegativeTestParams):
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_normal"] = {"k":negative_params.bad_init_func()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_optional"] = {"k":negative_params.bad_init_func()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_union"] = {"k":negative_params.bad_init_func()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_self_ref"] = {"k":negative_params.bad_init_func()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)

    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_normal"] = {123:negative_params.dic_init_func()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_optional"] = {123:negative_params.dic_init_func()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_union"] = {123:negative_params.dic_init_func()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_self_ref"] = {123:data.copy()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)
    
    # . . . . . . . . . . . . . . . . . . . . . . . . . . .
    data = initialize(dict, negative_params.dic_init_func)
    data["dict_any"] = {123:negative_params.dic_init_func()}

    with expect_type_error():
        from_dict(negative_params.cls, data, fd_check_types=True)

