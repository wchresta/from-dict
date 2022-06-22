import functools
from typing import Optional

from . import _from_dict

_original_function = _from_dict._get_constructor_type_hints
_cached_function: Optional['functools._lru_cache_wrapper'] = None

def cache_enable(max_size: int = 100):
    global _cached_function
    if _cached_function:
        if _cached_function.cache_info().maxsize == max_size:
            return
        _cached_function.cache_clear()
    _cached_function = functools.lru_cache(max_size)(_original_function)
    _from_dict._get_constructor_type_hints = _cached_function


def cache_disable():
    global _cached_function
    if _cached_function:
        _cached_function.cache_clear()
        _cached_function = None
    _from_dict._get_constructor_type_hints = _original_function

def cache_is_enabled() -> bool:
    return _cached_function is not None