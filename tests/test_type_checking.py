import copy
import datetime
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Type, Callable, TypeVar, Generic, Literal

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

TTestType = TypeVar("TTestType")
TSelfRef = TypeVar("TSelfRef")

@dataclass
class ClassBase(Generic[TTestType, TSelfRef]):
    normal: TTestType
    optional: Optional[TTestType]
    union: Union[str, NormalClass, DataClass, TTestType]
    any: Any
    self_ref: Optional[TSelfRef]

    list_normal: List[TTestType]
    list_optional: List[Optional[TTestType]]
    list_union: List[Union[str, NormalClass, DataClass, TTestType]]
    list_any: List[Any]
    list_self_ref: List[TSelfRef]
    
    dict_normal: Dict[str, TTestType]
    dict_optional: Dict[str, Optional[TTestType]]
    dict_union: Dict[str, Union[str, NormalClass, DataClass, TTestType]]
    dict_any: Dict[str, Any]
    dict_self_ref: Dict[str, TSelfRef]


ClassPrimitives = ClassBase[int, "ClassPrimitives"]
ClassDict = ClassBase[Dict[str,str], "ClassDict"]
ClassDictSimple = ClassBase[dict, "ClassDictSimple"]
ClassList = ClassBase[List[str], "ClassList"]
ClassDataClass = ClassBase[DataClass, "ClassDataClass"]
ClassNormalClass = ClassBase[NormalClass, "ClassNormalClass"]
ClassAttrClass = ClassBase[AttrClass, "ClassAttrClass"]
ClassListDataClass = ClassBase[List[DataClass], "ClassListDataClass"]
ClassDictDataClass = ClassBase[Dict[str, DataClass], "ClassDictDataClass"]
ClassLiteral = ClassBase[Literal["my-literal"], "ClassLiteral"]
ClassMultiLiteral = ClassBase[Literal[2, 3, 5, 7, 11], "ClassMultiLiteral"]

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

    pytest.param(NormTestParams(ClassLiteral, lambda: "my-literal", lambda: "my-literal"), id="literal-single"),
    pytest.param(NormTestParams(ClassMultiLiteral, lambda: 3, lambda: 3), id="literal-multi-1"),
    pytest.param(NormTestParams(ClassMultiLiteral, lambda: 11, lambda: 11), id="literal-multi-2"),
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

    pytest.param(NegativeTestParams(ClassLiteral, lambda: "my-literal", lambda: 1), id="literal-single"),
    pytest.param(NegativeTestParams(ClassMultiLiteral, lambda: 3, lambda: 1), id="literal-multi-1"),
    pytest.param(NegativeTestParams(ClassMultiLiteral, lambda: 5, lambda: 10), id="literal-multi-2"),
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
    data: dict = initialize(dict, norm_params.dic_init_func)
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
    data: dict = initialize(dict, norm_params.dic_init_func)
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
    data: dict = initialize(dict, negative_params.dic_init_func)
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

