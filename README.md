# from-dict
Create data structures from dictionaries.

## Features
* Transform dicts to `attr.s`, `dataclass` and `NamedTuple`
* Insert additional fields existing in dict into structure with `f__read_unknown=True`
* *Experimental* type-checking at runtime with `fd__type_check=True`

## Example
```python
import dataclasses
from from_dict import from_dict

@dataclasses.dataclass(frozen=True)
class MyDataclass:
    foo: int
    baz: str


input = {
    "foo": 22, 
    "baz": "Hello",
    "additional": "ignored key",
}

input_as_my_dataclass = from_dict(MyDataclass, input)
assert input_as_my_dataclass.foo == 22
assert input_as_my_dataclass.baz == "Hello"
```
