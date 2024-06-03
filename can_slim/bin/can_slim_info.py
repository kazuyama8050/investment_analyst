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
import traceback
import configparser
from argparse import ArgumentParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

current_script_path = os.path.abspath(__file__)
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
sys.path.append(os.path.join(app_dir, "lib"))

from batch_settings import BatchSettings
from db_handler import DbHandler
from date_format import DateFormat
from jp_symbol_handler import JpSymbolHandler
from usa_symbol_handler import UsaSymbolHandler
from symbol_handler import SymbolHandler
from finance_handler import FinanceHandler
from technical_handler import TechnicalHandler
from mail_handler import MailHandler


UPDATE_SYMBOL_EXECUTOR = "symbol"
UPDATE_FINANCE_EXECUTOR = "finance"
UPDATE_STOCK_EXECUTOR = "stock"

def get_options():
    usage = "usage: %prog (Argument-1) [options]"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-E", "--env", dest="env", action="store", help="env", default="dev", type=str)
    parser.add_argument("-t", "--target", dest="target", action="store", help="target", default=f"{UPDATE_SYMBOL_EXECUTOR},{UPDATE_FINANCE_EXECUTOR},{UPDATE_STOCK_EXECUTOR}", type=str)
    parser.add_argument("-p", "--process_num", dest="process_num", action="store", help="process_num", default=1, type=int)
    parser.add_argument("-c", "--country", dest="country", action="store", help="country", default="jp", type=str)
    return parser.parse_args()

options = get_options()

config = configparser.ConfigParser()
config.read(os.path.join(app_dir, "conf/can_slim_{}.conf".format(options.country)))
credentials_config = configparser.ConfigParser()
credentials_config.read(os.path.join(app_dir, "conf/credentials-" + options.env + ".conf"))

logger = BatchSettings.get_logger(app_dir, app_home)

today = datetime.today().date()
yesterday = today - relativedelta(days=1)
three_month_ago = today - relativedelta(months=3)
three_month_later = today + relativedelta(months=3)
default_report_date = DateFormat.string_to_date_format("1970-01-01")

COUNTRY = options.country

def main():
    try:
        target_list = options.target.split(",")
        if len(target_list) == 0:
            logger.info("not selected target")
            sys.exit()
        
        if options.country == "jp":
            countrySymbolHandler = JpSymbolHandler(config)
        elif options.country == "usa":
            countrySymbolHandler = UsaSymbolHandler(config)
            
        symbolHandler = SymbolHandler(config.get("output", "symbol_data_filepath"))
        
        """
        シンボル情報取得
        """
        if UPDATE_SYMBOL_EXECUTOR in target_list:
            logger.info("start download {} symbols.".format(COUNTRY))
            symbol_info_df = countrySymbolHandler.get_all_company_symbol()
            symbolHandler.update_symbol_list_csv(symbol_info_df)
            logger.info("download {} symbols done count={}".format(COUNTRY, len(symbol_info_df)))

        financeHandler = FinanceHandler(logger, config.get("output", "pl_data_filepath"))
        
        """
        ファイナンス情報取得
        """
        if UPDATE_FINANCE_EXECUTOR in target_list:
            all_symbols = symbolHandler.get_all_symbols()
            pl_updated_cnt = 0
            logger.info("start update pl data count = {0}".format(str(len(all_symbols))))
            pl_data_list = financeHandler.get_pl_data(all_symbols, options.process_num)
            financeHandler.write_pl_data_to_csv(pl_data_list)
            logger.info("finish update pl data, {0}symbols".format(str(len(all_symbols))))
                
        technicalHandler = TechnicalHandler(logger, config.get("symbol", "symbol_for_rs_term"), config.get("output", "termly_stock_data_filepath"))
        
        """
        株価情報取得
        """
        if UPDATE_STOCK_EXECUTOR in target_list:
            all_symbols = symbolHandler.get_all_symbols()
            stock_updated_cnt = 0
            logger.info("start update stock data, all symbol count = {}".format(str(len(all_symbols))))
            stock_data_list = technicalHandler.get_termly_stock_data(all_symbols, options.process_num)
            technicalHandler.write_termly_stock_data(stock_data_list)
            logger.info("finish update stock data, {0}symbols".format(str(len(all_symbols))))
        
    
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
        


if __name__ == "__main__":
    logger.info("start get_for_can_slim")
    main()
    logger.info("end get_for_can_slim")
