import os
import pickle
from uuid import uuid4


def multiprocess_safe_write(data, path):
    
    parent_dir = os.path.dirname(path)
    temp_name = f"{uuid4()}.tmp"
    with open(os.path.join(parent_dir, temp_name), "wb") as temp_file:
        pickle.dump(data, temp_file)

    os.rename(os.path.join(parent_dir, temp_name), path)
