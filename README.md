# from-dict
Create data structures from partially known dictionaries.

## Features
* Transform dicts to `attr.s`, `dataclass`, `NamedTuple`, and normal classes that have type-hints for all their __init__ parameters.
* Supports nested structures when using `typing.List` and `typing.Dict` type hints.
* Insert additional fields existing in dict into structure with `fd_copy_unknown=True`
* Optional run-time type-checking with `fd_check_types=True`
* Supports forward references


## Example
```python
from dataclasses import dataclass
from typing import List, Optional
from from_dict import from_dict


@dataclass(frozen=True)
class Preference:
    name: str
    score: int


@dataclass(frozen=True)
class Customer:
    name: str
    nick_name: Optional[str]
    preferences: List[Preference]


input_customer_data = {
    "name": "Christopher Lee",
    "nick_name": None,
    "preferences": [
        { "name": "The Hobbit", "score": 37 },
        { "name": "Count Dooku", "score": 2 },
        { "name": "Saruman", "score": 99 }
    ],
    "friend": "Mellon"
}

customer = from_dict(Customer, input_customer_data)
# Structured data is available as attributes since attr.s exposes them like that
assert customer.name == "Christopher Lee"
# Nested structures are also constructed. List[sub_strucutre] and Dict[key, sub_structure] are supported
assert customer.preferences[0].name == "The Hobbit"
# Data not defined in the strucutre is inserted into the __dict__ if possible
assert customer.__dict__["friend"] == "Mellon"
```

## Use cases

`from-dict` is especially useful when used on big and partially known data structures like JSON. Since undefined 
structure is ignored, we can use `from-dict` to avoid `try-catch` and `KeyError` hell:

Assume we want to interact with the Google GeoCoding API
(cf. https://developers.google.com/maps/documentation/geocoding/intro):

The JSON that is returned on requests contains some keys that we are not interested in. So we create 
data-structures that contain the keys that we actually want to use:

```python
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class AddressComponent:
    long_name: str
    short_name: str
    types: List[str]

@dataclass(frozen=True)
class Result:
    address_components: List[AddressComponent]
    formatted_address: str

@dataclass(frozen=True)
class Response:
    results: List[Result]
```

With that, given the `response` of the API, we can extract the fields and ignore everything else.

```python
from from_dict import from_dict

# This will throw a TypeError if something goes wrong.
structured_response: Response = from_dict(Response, 
                                          response, 
                                          fd_check_types=True,   # Do check types at run-time
                                          fd_copy_unknown=False  # Do not copy undefined data to __dict__
                                          )

# Now, we can access the data in a statically known manner
for res in structured_response.results:
    print(f"The formatted address is {res.formatted_address}")
    for addr_comp in res.address_components:
        print(f"Component {addr_comp.long_name}")

```
