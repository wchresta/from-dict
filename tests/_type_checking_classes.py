from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Literal

import attr

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