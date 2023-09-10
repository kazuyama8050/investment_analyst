import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib
import seaborn as sns
import mplfinance as mpf
# import talib as ta
import warnings
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import os, sys
import multiprocessing
import configparser
warnings.simplefilter('ignore')
plt.rcParams["font.size"] = 12
plt.rcParams['figure.figsize'] = (32.0, 10.0)
api_key='SRG6H2AQ57H9PSQ4'

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
sys.path.append(os.path.join(app_dir, "lib"))

config = configparser.ConfigParser()
config.read(os.path.join(app_dir, "conf/can_slim_usa.conf"))

from date_format import DateFormat
from symbol_handler import SymbolHandler
from finance_handler import FinanceHandler
from technical_handler import TechnicalHandler

today = datetime.today().date()
three_month_ago = today - relativedelta(months=3)
three_month_later = today + relativedelta(months=3)
default_report_date = DateFormat.string_to_date_format("1970-01-01")

MAIN_DF_FILEPATH = os.path.join(app_dir, config.get("dataset", "main_usa_dataset_path"))
MAIN_STOCK_DF_FILEPATH = os.path.join(app_dir, config.get("dataset", "main_usa_stock_dataset_path"))

def main():
    try:
        symbolHandler = SymbolHandler(config, default_report_date)
        df, write_flag = symbolHandler.get_all_company_symbol()
        if write_flag is True:
            symbolHandler.write_symbol_list(df)
        
        # df = pd.read_csv(MAIN_DF_FILEPATH)
        # df["latestClosingDate"] = df["latestClosingDate"].apply(lambda x: DateFormat.string_to_date_format(x) if x is not np.nan else default_report_date)
        # df = df.set_index("symbol", drop=False)
            
        # financeHandler = FinanceHandler(df, MAIN_DF_FILEPATH)
        # df = financeHandler.set_necessary_pl_data()
        # df.to_csv(MAIN_DF_FILEPATH, index = False)
        
        
        technicalHandler = TechnicalHandler(df, MAIN_STOCK_DF_FILEPATH, config.get("symbol", "symbol_for_rs_term"))
        df =technicalHandler.set_termly_stock_data()
        df.to_csv(MAIN_STOCK_DF_FILEPATH, index = False)
        
        df = pd.read_csv(MAIN_STOCK_DF_FILEPATH)
        df["is_valid"].fillna(0, inpace = True)
    
    
    except Exception as e:
        print("Error msg={}".format(e))




if __name__ == "__main__":
    print("start")
    main()
    print("end")
