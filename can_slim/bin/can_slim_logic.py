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
import traceback
from argparse import ArgumentParser

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
from jp_symbol_handler import JpSymbolHandler
from symbol_handler import SymbolHandler
from finance_handler import FinanceHandler
from technical_handler import TechnicalHandler
from mail_handler import MailHandler

def get_options():
    usage = "usage: %prog (Argument-1) [options]"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-E", "--env", dest="env", action="store", help="env", default="dev", type=str)
    parser.add_argument("-c", "--country", dest="country", action="store", help="country", default=JpSymbolHandler.JP_SYMBOL, type=str)
    return parser.parse_args()

options = get_options()

config = configparser.ConfigParser()
config.read(os.path.join(app_dir, "conf/can_slim_{}.conf".format(options.country)))
credentials_config = configparser.ConfigParser()
credentials_config.read(os.path.join(app_dir, "conf/credentials-" + options.env + ".conf"))

logger = BatchSettings.get_logger(app_dir, app_home)

today = datetime.today().date()
COUNTRY = options.country

def main():
    try:
        canslimLogicHandler = CanslimLogicHandler(logger)
        symbolHandler = SymbolHandler(config.get("output", "symbol_data_filepath"))
        financeHandler = FinanceHandler(logger, config.get("output", "pl_data_filepath"))
        technicalHandler = TechnicalHandler(logger, config.get("symbol", "symbol_for_rs_term"), config.get("output", "termly_stock_data_filepath"))
        
        finance_df = financeHandler.get_pl_data_from_csv()
        finance_df = finance_df.loc[finance_df["is_valid"] == 1]
        if len(finance_df) == 0:
            logger.info("not found valid finance data, option.country={}".format(COUNTRY))
            return
        
        calced_finance_df = canslimLogicHandler.mainLogic(finance_df)
        
        stock_df = technicalHandler.read_termly_stock_data()
        stock_df = stock_df.loc[stock_df["is_valid"] == 1]
        if len(stock_df) == 0:
            logger.info("not found valid stock data, option.country={}".format(COUNTRY))
            return
        
        calced_stock_df = canslimLogicHandler.relative_strength_logic(stock_df)
        
        finance_loose_result_symbols, rs_loose_result_symbols = judge_can_slim_loose_logic(calced_finance_df, calced_stock_df)
        finance_and_rs_loose_result_symbols = list(set(finance_loose_result_symbols) & set(rs_loose_result_symbols))
        
        finance_tight_result_symbols, rs_tight_result_symbols = judge_can_slim_tight_logic(calced_finance_df, calced_stock_df)
        finance_and_rs_tight_result_symbols = list(set(finance_tight_result_symbols) & set(rs_tight_result_symbols))
        
        symbol_infos_df = symbolHandler.read_all_symbol_infos()
        symbol_infos_df = symbol_infos_df[["symbol", "name"]]
        symbol_infos_df = symbol_infos_df.loc[symbol_infos_df["symbol"].isin(finance_loose_result_symbols)]
        symbol_infos = dict(zip(symbol_infos_df["symbol"], symbol_infos_df["name"]))
            
        if len(symbol_infos) == 0:
            logger.info("no symbol match of cansllim logic")
        
        finance_loose_result_symbol_infos = get_symbol_info_for_mail_template(finance_loose_result_symbols, symbol_infos)
        finance_and_rs_loose_result_symbol_infos = get_symbol_info_for_mail_template(finance_and_rs_loose_result_symbols, symbol_infos)
        finance_tight_result_symbol_infos = get_symbol_info_for_mail_template(finance_tight_result_symbols, symbol_infos)
        finance_and_rs_tight_result_symbol_infos = get_symbol_info_for_mail_template(finance_and_rs_tight_result_symbols, symbol_infos)
        
        mail_body_template = MailHandler.read_mail_body_template(os.path.join(app_dir, "mail", "can_slim_logic_mail_format.txt"))
        mail_body = mail_body_template.format(
            date = today,
            finance_and_rs_loose_results = finance_and_rs_loose_result_symbol_infos,
            finance_and_rs_tight_result = finance_and_rs_tight_result_symbol_infos,
            finance_loose_result = finance_loose_result_symbol_infos,
            finance_tight_result = finance_tight_result_symbol_infos
        )
        if MailHandler.send_mail(credentials_config.get("mail", "to_address"), "CANSLIM分析結果", mail_body) == False:
            raise Exception("error! send mail")
        logger.info("send email done")
        
    except Exception as e:
        logger.info(traceback.format_exc())
        
        # mail_body_template = MailHandler.read_mail_body_template(os.path.join(app_dir, "mail", "can_slim_system_error_mail_format.txt"))
        # mail_body = mail_body_template.format(
        #     date = today,
        #     app_name = app_home,
        #     error_msg = traceback.format_exc()
        # )
        # MailHandler.send_mail(credentials_config.get("mail", "to_address"), "CANSLIMシステムエラー通知", mail_body)
        
        sys.exit(1)
        
def get_symbol_info_for_mail_template(symbol_list, symbol_infos):
    necessary_symbol_info = ""
    for symbol in symbol_list:
        if necessary_symbol_info != "":
            necessary_symbol_info = necessary_symbol_info + "\n"
        necessary_symbol_info = necessary_symbol_info + symbol + ":" + symbol_infos[symbol]
        
    return necessary_symbol_info
        
def judge_can_slim_loose_logic(finance_df, stock_df):
    finance_df = finance_df.loc[finance_df["quarterly_eps_clear_seg"] >= 1]
    finance_df = finance_df.loc[finance_df["quarterly_revenue_clear_seg"] >= 2]
    finance_df = finance_df.loc[finance_df["yearly_eps_clear_seg"] >= 3]
    finance_df = finance_df.loc[finance_df["latest_year_roe"] >= 17]
    
    stock_df = stock_df.loc[stock_df["rs"] >= 80]
    
    finance_result_symbols = list(finance_df["symbol"].unique())
    rs_result_symbols = list(stock_df["symbol"].unique())
    
    return finance_result_symbols, rs_result_symbols
        
def judge_can_slim_tight_logic(finance_df, stock_df):
    finance_df = finance_df.loc[finance_df["quarterly_eps_clear_seg"] >= 2]
    finance_df = finance_df.loc[finance_df["quarterly_revenue_clear_seg"] >= 3]
    finance_df = finance_df.loc[finance_df["yearly_eps_clear_seg"] >= 4]
    finance_df = finance_df.loc[finance_df["latest_year_roe"] >= 25]
    
    stock_df = stock_df.loc[stock_df["rs"] >= 90]
    
    finance_result_symbols = list(finance_df["symbol"].unique())
    rs_result_symbols = list(stock_df["symbol"].unique())
    
    return finance_result_symbols, rs_result_symbols
    

def get_db_connection(db_config, db_name):
    db = DbHandler().get_instance()
    db.set_session(db_config, db_name)
    return db
    
if __name__ == "__main__":
    print("start can_slim_logic")
    main()
    print("end can_slim_logic")
