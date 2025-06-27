import pickle
from typing import Callable, Optional, Any


def vaex_df_handler(obj: Any) -> Any:
    if hasattr(obj, '__class__') and 'vaex' in obj.__class__.__module__:
        try:
            import vaex
            if isinstance(obj, vaex.dataframe.DataFrame):
                return obj.fingerprint()
        except ImportError:
            raise ImportError("Object requiring pickling appears to be a vaex DataFrame, but vaex is not installed. "
                              "Is this handler broken")
    
    return None


def psycopg2_connection_handler(obj: Any) -> Any:
    if hasattr(obj, '__class__') and hasattr(obj, 'dsn'):
        try:
            import psycopg2
            if isinstance(obj, psycopg2.extensions.connection):
                info = obj.info
                return {
                    'host': info.host,
                    'port': info.port, 
                    'dbname': info.dbname,
                    'user': info.user,
                    'status': obj.status
                }               
        except ImportError:
            raise ImportError("Object requiring pickling appears to be a psycopg2 connection, but psycopg2 is "
                              "not installed. Is this handler broken")
    
    return None


def huggingface_model_handler(obj: Any) -> Any:
    if not hasattr(obj, '__class__'):
        return None
        
    module_name = obj.__class__.__module__
    if not ('transformers' in module_name or 'sentence_transformers' in module_name):
        return None
    
    model_info = {
        'model_repr': repr(obj),  # Architecture + config info
    }
    
    # Weight sample to distinguish fine-tunes  
    if hasattr(obj, 'state_dict'):
        state_dict = obj.state_dict()
        param_names = list(state_dict.keys())
        if param_names:
            first_param = state_dict[param_names[0]].flatten()[0].item()
            last_param = state_dict[param_names[-1]].flatten()[-1].item()
            model_info['weight_sample'] = (first_param, last_param)
            
    return model_info


class PickleSubstituteHandler:
    """
    Creates deterministic identifiers for objects that cannot be deterministically serialized with pickle or dill.
    """

    edge_case_handlers = []

    def __init__(self):
        raise RuntimeError("This class is not meant to be instantiated. Use the class methods directly.")
    
    @classmethod
    def dumps(cls, obj: Any, use_dill: bool = False) -> bytes:
        """        
        Serialize or, create a deterministic identifier for objects that cannot be deterministically serialized.
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
PickleSubstituteHandler.register_pickle_substitute_handler(psycopg2_connection_handler)
PickleSubstituteHandler.register_pickle_substitute_handler(huggingface_model_handler)
