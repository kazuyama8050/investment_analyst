import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pandas_datareader.data as web
import yfinance as yf
import japanize_matplotlib
import seaborn as sns
import warnings
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import os, sys
import configparser

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
sys.path.append(os.path.join(app_dir, "lib"))

config_usa = configparser.ConfigParser()
config_usa.read(os.path.join(app_dir, "conf/can_slim_usa.conf"))
config_jp = configparser.ConfigParser()
config_jp.read(os.path.join(app_dir, "conf/can_slim_jp.conf"))

from can_slim_logic_handler import CanslimLogicHandler


MAIN_USA_DF_FILEPATH = os.path.join(app_dir, config_usa.get("dataset", "main_usa_dataset_path"))
MAIN_USA_STOCK_DF_FILEPATH = os.path.join(app_dir, config_usa.get("dataset", "main_usa_stock_dataset_path"))
CLEAR_USA_DF_FILEPATH = os.path.join(app_dir, config_usa.get("dataset", "clear_usa_dataset_path"))
CLEAR_USA_STOCK_DF_FILEPATH = os.path.join(app_dir, config_usa.get("dataset", "clear_usa_stock_dataset_path"))
MAIN_JP_DF_FILEPATH = os.path.join(app_dir, config_jp.get("dataset", "main_jp_dataset_path"))
CLEAR_JP_DF_FILEPATH = os.path.join(app_dir, config_jp.get("dataset", "clear_jp_dataset_path"))
MAIN_JP_STOCK_DF_FILEPATH = os.path.join(app_dir, config_jp.get("dataset", "main_jp_stock_dataset_path"))
CLEAR_JP_STOCK_DF_FILEPATH = os.path.join(app_dir, config_jp.get("dataset", "clear_jp_stock_dataset_path"))

def main():
    jp_finance_df = pd.read_csv(MAIN_JP_DF_FILEPATH)
    jp_finance_df = get_valid_df(jp_finance_df)
    
    jp_stock_df = pd.read_csv(MAIN_JP_STOCK_DF_FILEPATH)
    jp_stock_df = get_valid_df(jp_stock_df)
    
    canslimLogicHandler = CanslimLogicHandler(jp_finance_df, jp_stock_df)
    write_relative_strength_dataset(canslimLogicHandler, CLEAR_JP_STOCK_DF_FILEPATH)
    
    
def write_main_clear_dataset(canslimLogicHandler, output):
    df = canslimLogicHandler.mainLogic()
    df = df.loc[(df["quarterly_eps_clear_seg"] >= 2) & (df["quarterly_revenue_clear_seg"] >= 3) & \
        (df["yearly_eps_clear_seg"] >= 3) & (df["latest_year_roe"] >= canslimLogicHandler.yearly_roe_clear_val)]
    print(len(df))
    print(df)
    df.to_csv(output, index=False)
    
def write_relative_strength_dataset(canslimLogicHandler, output):
   df = canslimLogicHandler.relative_strength_logic()
#    df = df.loc[df["rs"] >= 70]
   print(len(df))
   print(df)
   df.to_csv(output, index=False)
    
def get_valid_df(df):
    df["is_valid"].fillna(0, inplace = True)
    df = df.loc[df["is_valid"] == 1]
    return df
    


if __name__ == "__main__":
    print("start")
    main()
    print("end")
