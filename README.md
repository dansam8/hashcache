# hashcache

**Simple disk-based function result caching using Python decorators.**

`hashcache` is a lightweight, caching decorator that stores function results to disk based on their arguments.

**The goal**

Lightweight, easy to interpret (no complex eviction policies) and fast. Originally designed for caching stages of data processing pipelines, but can be used for any function 👀.

---

## 🔧 Installation

```bash
pip install hashcache
```

## Quick start

```python
from hashcache import hashcache
import time

@hashcache("cache_dir")  # defaults to "/tmp/hashcache"
def f(value):
    time.sleep(1)
    return value

print(f(1))  # First call takes 1s
print(f(1))  # Second call returns instantly from cache
print(f(1, use_cache=False))  # Bypass cache, takes 1s again
```

## Cache Control Arguments

The Decorator extracts the following args from the function call
    (they will not be passed onwards to the function):

| Argument      | Type | Default | Description                                                                             |
|---------------|------|---------|-----------------------------------------------------------------------------------------|
| use_cache     | bool | True    | Skip or use the cache                                                                   |
| refresh_cache | bool | False   | Force re-computation and overwrite cache                                                |
| cache_nonce   | Any  | None    | Used to get multiple results from a non-deterministic function with the same arguments. |
| use_dill      | bool | False   | Use `dill` for serialization instead of `pickle`.                                       |

## Limitation (Important!)

By default, the cache key is generated using pickle, which does not include class method definitions. This will lead to stale cache results if the behavior of a class method changes.

```python
from hashcache import hashcache

class MyClass:
    def f(self):
        return 1

@hashcache()
def g(obj: MyClass):
    return obj.f()

# Returns 1
print(g(MyClass())) 

# Redefine method after caching
def f(self):
    return 2

MyClass.f = f

# Still returns 1 (cached)
print(g(MyClass())) 

# Returns 2, uses dill for accurate function serialization
# But much slower
print(g(MyClass(), use_dill=True))
```
