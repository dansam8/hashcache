import os
import hashlib
import pickle
from functools import wraps
import logging
from typing import Any, Callable

from .utils import multiprocess_safe_write
from .pickle_substitute_handlers import PickleSubstituteHandler

        
def hashcache(
    cache_dir="_hashcache_dir", 
    use_cache_default=True,
    refresh_cache_default=False, 
    use_dill_for_keys_default=False
):

    """
    Important Note: 
    This decorator is not aware of the function code it wraps, if that code changes the cache must be refreshed 
    or deleted manually.

    Important Limitation: 
    Due to limitations in Python's pickle module, when a class instance is passed as an argument to a function 
    decorated with @hashcache, the function code of that class is not included in the cache key. As a result, 
    if the class's methods are later modified, the cache will return outdated results based on the previous 
    definition.

    Decorator that caches the result of a function based on the function's arguments.
    The Decorator extracts the following args from the function call
    (they will not be passed onwards to the function):

    - use_cache: bool, default=True. If False, the function will not use the cache.
    - refresh_cache: bool, default=False. If True, the function will refresh the cache.
    - cache_nonce: Any, default=None. Unique identifier to create distinct 
      cache entries for identical arguments. Useful for non-deterministic 
      functions, generating multiple results for the same inputs.
    - use_dill_for_keys: bool, default=False. If True, the cache_keys will be generated using dill instead of 
      pickle to solve the limitation mentioned above. However Dill is much slower than pickle.
    """

    if not isinstance(cache_dir, str):
        raise TypeError(
            "directory must be a string representing the path to the cache directory."
            "Did you forget to call the decorator?"
        )
    
    os.makedirs(cache_dir, exist_ok=True)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            *args, 
            use_cache: bool=use_cache_default, 
            refresh_cache: bool=refresh_cache_default, 
            use_dill_for_keys: bool=use_dill_for_keys_default, 
            cache_nonce: Any=None,
            **kwargs
        ):

            cache_keys = [func.__module__, func.__name__, args, kwargs, cache_nonce]
            pickled_cache_keys = PickleSubstituteHandler.dumps(cache_keys, use_dill=use_dill_for_keys)
            hashed_cache_keys = hashlib.sha256(pickled_cache_keys).hexdigest()

            cache_path = os.path.join(cache_dir, f"{hashed_cache_keys}.pkl")

            if use_cache and not refresh_cache and os.path.exists(cache_path):
                try:
                    with open(cache_path, "rb") as file:
                        result = pickle.load(file)
                        return result
                except (EOFError, pickle.PickleError):
                    logging.getLogger(__name__).warning(
                        f"Cache file {cache_path} is corrupted or empty. Recomputing result.")
                    
            result = func(*args, **kwargs)
            multiprocess_safe_write(result, cache_path)

            return result
        
        return wrapper
    
    return decorator
