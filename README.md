# hashcache

**Simple disk-based function result caching using Python decorators.**

`hashcache` is a lightweight, caching decorator that stores function results to disk based on their arguments.

**The goal**

Lightweight, minimalist, easy to interpret (no complex eviction policies) and fast. Originally designed for caching stages of data processing pipelines, but can be used for any function 👀.

---

## Installation

```bash
pip install hashcache
```

## Quick start

```python
from hashcache import hashcache
import time

@hashcache()
def f(value):
    time.sleep(1)
    return value

print(f(1))  # First call takes 1s
print(f(1))  # Second call returns instantly from cache
print(f(1, use_cache=False))  # Bypass cache, takes 1s again
```

### Clearing the cache

The intention of this library is minimalism and simplicity, so there is no built-in cache management. The cache should be cleared periodically and after potentially breaking changes to the code

```bash
rm -r _hashcache_dir
```


## Cache Control Arguments

The Decorator extracts the following args from the function call
    (they will not be passed onwards to the function):

| Argument          | Type | Default | Description                                                                             |
|-------------------|------|---------|-----------------------------------------------------------------------------------------|
| use_cache         | bool | True    | Skip or use the cache                                                                   |
| refresh_cache     | bool | False   | Force re-computation and overwrite cache                                                |
| cache_nonce       | Any  | None    | Used to get multiple results from a non-deterministic function with the same arguments. |
| use_dill_for_keys | bool | False   | Use `dill` for serialization instead of `pickle`.                                       |


## Limitation (Important!)

By default, the cache key is generated using pickle, which does not include class method definitions. This will lead to stale cache results if the behavior of a class method changes.

```python
from hashcache import hashcache

class MyClass:
    def method(self):
        return "original result"

@hashcache()
def function_with_cache(obj: MyClass):
    return obj.method()

# Returns original result
print(function_with_cache(MyClass())) 

# Redefine method after caching
def method(self):
    return "updated result"

MyClass.method = method

# Still returns "original result" (cached)
print(function_with_cache(MyClass())) 

# Returns "updated result", uses dill for accurate function serialization
# But much slower
print(function_with_cache(MyClass(), use_dill_for_keys=True))
```
