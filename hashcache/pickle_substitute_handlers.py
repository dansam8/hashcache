import io
import pickle
from typing import Callable, Optional, Any


def vaex_df_handler(obj: Any) -> Any:
    if hasattr(obj, '__class__') and 'vaex' in obj.__class__.__module__:
        try:
            import vaex
            if isinstance(obj, vaex.dataframe.DataFrame):
                return obj.fingerprint()
        except ImportError:
            raise ImportError("Object requiring picking appears to be a vaex DataFrame, but vaex is not installed. Is this handler broken")
    
    return None


class PickleSubstituteHandler:
    """
    Creates deterministic identifiers for objects that otherwise cannot be deterministically serialized with pickle or dill.
    """

    edge_case_handlers = []

    def __init__(self):
        raise RuntimeError("This class is not meant to be instantiated. Use the class methods directly.")
    
    @classmethod
    def dumps(cls, obj: Any, use_dill: bool = False) -> bytes:
        """        
        Serialize or create a deterministic identifier for objects that cannot be deterministically serialized.
        """
        
        def _preprocess_for_hashing(obj):
            # Check if any handlers want to replace this object
            for handler in cls.edge_case_handlers:
                result = handler(obj)
                if result is not None:
                    return result 
            
            # Recursively process containers
            if isinstance(obj, (list, tuple)):
                return type(obj)(_preprocess_for_hashing(item) for item in obj)
            elif isinstance(obj, dict):
                return {k: _preprocess_for_hashing(v) for k, v in obj.items()}
            
            return obj
        
        processed_cache_keys = _preprocess_for_hashing(obj)

        if use_dill:
            try:
                import dill
                return dill.dumps(processed_cache_keys)
            except ImportError:
                raise ImportError("Dill is not installed. Please install it to use the use_dill option.")
        else:
            return pickle.dumps(processed_cache_keys)

    @classmethod
    def register_pickle_substitute_handler(cls, handler: Callable[[Any], Optional[Any]]) -> None:
        """
        Register a custom edge case handler for specific object types.
        """
        cls.edge_case_handlers.append(handler)


PickleSubstituteHandler.register_pickle_substitute_handler(vaex_df_handler)
