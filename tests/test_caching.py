import time
import sys
from dataclasses import dataclass

from typing import List, Dict

import pytest
from from_dict import from_dict

# ...................................................................
# These allow the test to disable caching so we can verify the 
# performance gains.

import from_dict._from_dict as _fd
hints_cached_func  = _fd.get_constructor_type_hints
hints_wrapped_func  = _fd.get_constructor_type_hints.__wrapped__

fwd_ref_cached_func  = _fd._resolve_str_forward_ref
fwd_ref_wrapped_func = _fd._resolve_str_forward_ref.__wrapped__

def cache_disable():
    global hints_wrapped_func
    global fwd_ref_wrapped_func
    _fd.get_constructor_type_hints = hints_wrapped_func
    _fd._resolve_str_forward_ref = fwd_ref_wrapped_func

def cache_is_enabled():
    return _fd.get_constructor_type_hints == hints_cached_func

def cache_enable():
    global hints_cached_func
    global fwd_ref_cached_func
    _fd.get_constructor_type_hints = hints_cached_func
    _fd._resolve_str_forward_ref = fwd_ref_cached_func
    hints_cached_func.cache_clear()
    fwd_ref_cached_func.cache_clear()

# ...................................................................

@dataclass(frozen=True)
class MainData:
    name: str
    id: int
    date: str
    inner: List['InnerData']
    properties: Dict[str, str]


@dataclass(frozen=True)
class InnerData:
    name: str
    result: bool
    tags: List[str]

def test_cache_speed_improvement():
    test_data =  {
        'name': 'root', 
        'id': 12324, 
        'date': '2022-04-06T010203', 
        'inner': [
            {'name': 'Run-1', 'result': True, 'tags': ['rc']}, 
            {'name': 'Run-2', 'result': False, 'tags': ['nighty']},
            {'name': 'Run-3', 'result': True, 'tags': ['nighty']}, 
            {'name': 'Run-4', 'result': True, 'tags': ['official']}
        ], 
        'properties': {
            'prop-1': 'value', 
            'prop-2': 'value',
            'prop-3': 'value', 
            'prop-4': 'value', 
            'prop-5': 'value'
        }
    }
    cache_disable()
    assert not cache_is_enabled()
    disabled_time = _get_time_for_x_calls(test_data)
    
    cache_enable()
    assert cache_is_enabled()
    enabled_time = _get_time_for_x_calls(test_data)
    print(f"Improvement = {disabled_time / enabled_time:0.2f}")
    assert (disabled_time / enabled_time) > 2.0

    cache_disable()
    assert not cache_is_enabled()
    disabled_time = _get_time_for_x_calls(test_data)
    cache_enable()
    assert disabled_time > (enabled_time * 2)

def _get_time_for_x_calls(test_data: dict):
    start_time = time.time()
    LOOPS = 1_000
    for _ in range(LOOPS):
        from_dict(MainData, test_data)
    elapsed = time.time() - start_time
    print(f"Took {elapsed:0.3f} seconds for {LOOPS} calls")
    return elapsed