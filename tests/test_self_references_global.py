from typing import Optional, List, Dict

import sys

from from_dict import from_dict

if sys.version_info[:2] >= (3, 7):
    from dataclasses import dataclass
    GLOBALS = None # Don't need globals()
else:
    from attr import dataclass
    GLOBALS = globals()

if sys.version_info[:2] >= (3, 9):
    LIST = list
else:
    LIST = List


@dataclass
class LinkListNode:
    name: str
    next: 'LinkListNode'

@dataclass
class TreeNode:
    name: str
    children: LIST['TreeNode']

@dataclass
class LinkListNode2:
    name: str
    next: Optional['LinkListNode2'] 


@dataclass
class DictNode:
    name: str
    children: Dict[str, 'DictNode']

def test_self_ref():
    data = {"name": "n1", "next": {"name": "n2", "next": None}}
    # Can't type check because next is not optional 
    node = from_dict(LinkListNode, data, fd_global_ns=GLOBALS)
    assert node.name == "n1"
    assert node.next.name == "n2"


def test_self_ref_in_list():
    data = {"name": "n1", "children": [{"name": "n2", "children": []}]}
    node = from_dict(TreeNode, data, fd_check_types=True, fd_global_ns=GLOBALS)
    assert node.name == "n1"
    assert node.children[0].name == "n2"


def test_self_ref_in_optional():
    data = {"name": "n1", "next": {"name": "n2", "next": None}}
    node = from_dict(LinkListNode2, data, fd_check_types=True, fd_global_ns=GLOBALS)
    assert node.name == "n1"
    assert node.next.name == "n2"


def test_self_ref_in_dict():
    data = {
        "name": "n1", 
        "children": {
            "id-123": {"name": "n2", "children": {}},
            "id-456": {"name": "n3", "children": {}}
        }
    }
    node = from_dict(DictNode, data, fd_check_types=True, fd_global_ns=GLOBALS)
    assert node.name == "n1"
    assert node.children["id-123"].name == "n2"
    assert node.children["id-456"].name == "n3"