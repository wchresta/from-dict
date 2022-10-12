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
        {"name": "The Hobbit", "score": 37},
        {"name": "Count Dooku", "score": 2},
        {"name": "Saruman", "score": 99}
    ],
    "friend": "Mellon"
}


def test_readme():
    customer = from_dict(Customer, input_customer_data)
    # Structured data is available as attributes since attr.s exposes them like that
    assert customer.name == "Christopher Lee"
    # Nested structures are also constructed. List[sub_strucutre] and Dict[key, sub_structure] are supported
    assert customer.preferences[0].name == "The Hobbit"
    # Data not defined in the strucutre is inserted into the __dict__ if possible
    assert customer.__dict__["friend"] == "Mellon"
