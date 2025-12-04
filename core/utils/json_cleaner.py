import pandas as pd
import numpy as np
from datetime import datetime, date

def clean_for_json(obj):
    if isinstance(obj, list):
        return [clean_for_json(o) for o in obj]

    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}

    # Fix pandas Series explicitly
    if isinstance(obj, pd.Series):
        return obj.to_dict()

    # Fix numpy data types
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.ndarray, list)):
        return obj.tolist()

    # Fix timestamps
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    return obj
