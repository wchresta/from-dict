import time
import sys

from typing import List, Dict

import pytest
from from_dict import from_dict, cache_disable, cache_enable, cache_is_enabled

if sys.version_info[:2] >= (3, 7):
    from dataclasses import dataclass
    GLOBALS = None # Don't need globals()
else:
    from attr import dataclass
    GLOBALS = globals()


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
    if sys.version_info[:2] == (3, 6):
        pytest.skip("Python 3.6 requires the use of globals(). This disabled caching.")
    
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
    disabled_count = _get_calls_per_second(test_data)
    
    cache_enable()
    assert cache_is_enabled()
    enabled_count = _get_calls_per_second(test_data)
    print(f"Improvement = {enabled_count / disabled_count:0.2f}")
    assert (enabled_count / disabled_count) > 2.0

    cache_disable()
    assert not cache_is_enabled()
    disabled_count = _get_calls_per_second(test_data)
    assert disabled_count < (enabled_count / 2)


def _get_calls_per_second(test_data: str):
    count = 0
    end_time = time.time() + 1
    while time.time() < end_time:
        from_dict(MainData, test_data)
        count +=1 
    print(f"There were {count:,} calls per second")
    return count