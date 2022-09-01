import os
import datetime
from dataclasses import dataclass

import from_dict._from_dict as _fd

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

def new_empty_namespaces():
    return _fd.NamespaceTypes(None, None)

def test_empty():
    obj1 = new_empty_namespaces()
    obj2 = new_empty_namespaces()
    assert (obj1 == obj2)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

def new_simple_namespaces():
    return _fd.NamespaceTypes(globals(), locals())

def test_simple():
    obj1 = new_simple_namespaces()
    obj2 = new_simple_namespaces()
    assert (obj1 == obj2)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

def new_with_changing_locals():
    r = os.urandom(2)
    d = datetime.datetime.now()
    return _fd.NamespaceTypes(globals(), locals())


def test_with_changing_locals():
    obj1 = new_with_changing_locals()
    obj2 = new_with_changing_locals()
    assert (obj1 == obj2)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

def new_with_global_in_locals():
    g = globals()
    return _fd.NamespaceTypes(g, locals())

def test_with_global_in_locals():
    obj1 = new_with_global_in_locals()
    obj2 = new_with_global_in_locals()
    assert (obj1 == obj2)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

def new_with_local_in_locals():
    ''' local self reference '''
    g = globals()
    l = locals()
    return _fd.NamespaceTypes(g, locals())

def test_with_local_in_locals():
    obj1 = new_with_local_in_locals()
    obj2 = new_with_local_in_locals()
    assert (obj1 == obj2)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

def new_with_nested_dataclass():
    @dataclass 
    class NestedDC:
        name: str
    return _fd.NamespaceTypes(globals(), locals())

def test_with_nested_dataclass():
    ''' NOTE: This test expects that the namespaces are NOT equal 
    '''
    obj1 = new_with_nested_dataclass()
    obj2 = new_with_nested_dataclass()
    assert (obj1 != obj2)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

@dataclass
class DummyClass1:
    name: str
    value: int

def new_with_nested_global_dataclass():
    dc = DummyClass1
    return _fd.NamespaceTypes(globals(), locals())

def test_with_nested_global_dataclass():
    obj1 = new_with_nested_global_dataclass()
    obj2 = new_with_nested_global_dataclass()
    assert isinstance(obj2.local_types, dict)
    assert obj2.local_types["dc"]  == DummyClass1
    assert (obj1 == obj2)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

def new_with_nested_module_dataclass():
    from json import JSONDecoder
    return _fd.NamespaceTypes(globals(), locals())

def test_with_nested_module_dataclass():
    obj1 = new_with_nested_module_dataclass()
    obj2 = new_with_nested_module_dataclass()
    assert isinstance(obj2.local_types, dict)
    assert obj2.local_types["JSONDecoder"].__name__  == "JSONDecoder"
    assert (obj1 == obj2)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

@dataclass
class DummyClass2:
    name: str
    value: int

@dataclass
class DummyClass3:
    name: str
    value: int

def new_with_copy_of_namespaces():
    return _fd.NamespaceTypes(globals().copy(), locals().copy())

def test_with_copy_of_namespaces():
    obj1 = new_with_copy_of_namespaces()
    obj2 = new_with_copy_of_namespaces()
    assert (obj1 == obj2)

    globals()["DummyClass2"] = DummyClass3
    obj2 = new_with_copy_of_namespaces()
    assert (obj1 != obj2)
