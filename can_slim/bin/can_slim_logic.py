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
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
sys.path.append(os.path.join(app_dir, "lib"))

from batch_settings import BatchSettings
from db_handler import DbHandler
from date_format import DateFormat
from can_slim_logic_handler import CanslimLogicHandler
from finance_db_handler import FinanceDbHandler
from technical_db_handler import TechnicalDbHandler
from jp_symbol_handler import JpSymbolHandler

options = BatchSettings.get_options()

config_usa = configparser.ConfigParser()
config_usa.read(os.path.join(app_dir, "conf/can_slim_usa.conf"))
config_jp = configparser.ConfigParser()
config_jp.read(os.path.join(app_dir, "conf/can_slim_jp.conf"))
credentials_config = configparser.ConfigParser()
credentials_config.read(os.path.join(app_dir, "conf/credentials-" + options.env + ".conf"))

logger = BatchSettings.get_logger(app_dir, app_home)

def main():
    try:
        db = get_db_connection(credentials_config, "investment_analyst")
        session = db.get_session()
        
        financeDbHandler = FinanceDbHandler(session)
        technicalDbHandler = TechnicalDbHandler(session)
        canslimLogicHandler = CanslimLogicHandler(logger)
        
        finance_data = financeDbHandler.find_valid_finances(JpSymbolHandler.JP_SYMBOL)
        finance_df = pd.DataFrame(finance_data)
        calced_finance_df = canslimLogicHandler.mainLogic(finance_df)
        
        stock_data = technicalDbHandler.find_valid_stocks(JpSymbolHandler.JP_SYMBOL)
        stock_df = pd.DataFrame(stock_data)
        calced_stock_df = canslimLogicHandler.relative_strength_logic(stock_df)
        
        finance_result_symbols, rs_result_symbols = judge_can_slim_loose_logic(calced_finance_df, calced_stock_df)
        print(finance_result_symbols)
        print(rs_result_symbols)
        
    except Exception as e:
        session.rollback()
        db.close_session()
        raise("Error msg={}".format(e))
        logger.info(traceback.format_exc())
        
def judge_can_slim_loose_logic(finance_df, stock_df):
    finance_df = finance_df.loc[finance_df["quarterly_eps_clear_seg"] >= 1]
    finance_df = finance_df.loc[finance_df["quarterly_revenue_clear_seg"] >= 2]
    finance_df = finance_df.loc[finance_df["yearly_eps_clear_seg"] >= 3]
    finance_df = finance_df.loc[finance_df["latest_year_roe"] >= 17]
    
    stock_df = stock_df.loc[stock_df["rs"] >= 80]
    
    finance_result_symbols = list(finance_df["symbol"].unique())
    rs_result_symbols = list(stock_df["symbol"].unique())
    
    return finance_result_symbols, rs_result_symbols
    
    
def get_options():
    usage = "usage: %prog (Argument-1) [options]"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-E", "--env", dest="env", action="store", help="env", default="dev", type=str)
    return parser.parse_args()

def get_db_connection(db_config, db_name):
    db = DbHandler().get_instance()
    db.set_session(db_config, db_name)
    return db
    
if __name__ == "__main__":
    print("start can_slim_logic")
    main()
    print("end can_slim_logic")
