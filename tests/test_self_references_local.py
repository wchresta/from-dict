
from typing import Optional, List, Dict

import sys

from from_dict import from_dict

if sys.version_info[:2] >= (3, 7):
    from dataclasses import dataclass
else:
    from attr import dataclass

if sys.version_info[:2] >= (3, 9):
    LIST = list
else:
    LIST = List


def test_local_self_ref():
    @dataclass
    class Node:
        name: str
        next: 'Node'

    data = {"name": "n1", "next": {"name": "n2", "next": None}}
    node = from_dict(Node, data, fd_local_ns=locals())
    assert node.name == "n1"
    assert node.next.name == "n2"

def test_local_self_ref_in_list():
    @dataclass
    class Node:
        name: str
        children: LIST['Node']

    data = {"name": "n1", "children": [{"name": "n2", "children": []}]}
    node = from_dict(Node, data, fd_check_types=True, fd_local_ns=locals())
    assert node.name == "n1"
    assert node.children[0].name == "n2"


def test_local_self_ref_in_optional():
    @dataclass
    class Node:
        name: str
        next: Optional['Node']

    data = {"name": "n1", "next": {"name": "n2", "next": None}}
    node = from_dict(Node, data, fd_check_types=True, fd_local_ns=locals())
    assert node.name == "n1"
    assert node.next.name == "n2"

    
def test_local_self_ref_in_dict():
    @dataclass
    class Node:
        name: str
        children: Dict[str, 'Node']

    data = {
        "name": "n1", 
        "children": {
            "id-123": {"name": "n2", "children": {}},
            "id-456": {"name": "n3", "children": {}}
        }
    }
    node = from_dict(Node, data, fd_check_types=True, fd_local_ns=locals())
    assert node.name == "n1"
    assert node.children["id-123"].name == "n2"
    assert node.children["id-456"].name == "n3"