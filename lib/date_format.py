import os,sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

class DateFormat:

    @staticmethod
    def string_to_date_format(date_str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    
    @staticmethod
    def timestamp_to_date_format(timestamp):
        return timestamp.to_pydatetime().date()
    
    @staticmethod
    def date_to_string_format(date_obj):
        return date_obj.strftime("%Y-%m-%d")
    
    @staticmethod
    def date_to_datetime_format(date_obj):
        return datetime(date_obj.year, date_obj.month, date_obj.day)
    
    @staticmethod
    def date_to_datetimeindex_format(date_obj):
        return pd.to_datetime(date_obj)
    
    @staticmethod
    def date_to_datetime64_format(date_obj):
        return np.datetime64(date_obj)