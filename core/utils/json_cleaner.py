# core/utils/json_cleaner.py

import pandas as pd
import datetime

def clean_for_json(obj):
    """
    Recursively convert Pandas Timestamp, numpy values,
    and datetimes into JSON serializable types.
    """
    if isinstance(obj, pd.Timestamp):
        return obj.to_pydatetime().isoformat()

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    if isinstance(obj, datetime.date):
        return obj.isoformat()

    if isinstance(obj, list):
        return [clean_for_json(i) for i in obj]

    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}

    return obj
