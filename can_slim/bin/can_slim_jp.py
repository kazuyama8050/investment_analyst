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
from symbol_handler import SymbolHandler
from finance_handler import FinanceHandler
from finance_db_handler import FinanceDbHandler
from technical_handler import TechnicalHandler
from technical_db_handler import TechnicalDbHandler
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
    return parser.parse_args()

options = get_options()

config = configparser.ConfigParser()
config.read(os.path.join(app_dir, "conf/can_slim_jp.conf"))
credentials_config = configparser.ConfigParser()
credentials_config.read(os.path.join(app_dir, "conf/credentials-" + options.env + ".conf"))

logger = BatchSettings.get_logger(app_dir, app_home)

today = datetime.today().date()
yesterday = today - relativedelta(days=3)
three_month_ago = today - relativedelta(months=3)
three_month_later = today + relativedelta(months=3)
default_report_date = DateFormat.string_to_date_format("1970-01-01")



def main():
    try:
        target_list = options.target.split(",")
        if len(target_list) == 0:
            logger.info("not selected target")
            sys.exit()
        
        db = get_db_connection(credentials_config, "investment_analyst")
        session = db.get_session()
        
        jpSymbolHandler = JpSymbolHandler(config)
        symbolHandler = SymbolHandler(session)
        
        if UPDATE_SYMBOL_EXECUTOR in target_list:
            logger.info("start upsert jp symbols")
            symbol_info_list = jpSymbolHandler.get_all_company_symbol()
            symbolHandler.update_symbol_list(symbol_info_list)
            session.commit()
            logger.info("upsert jp symbols done count={}".format(len(symbol_info_list)))

        financeHandler = FinanceHandler(logger)
        financeDbHandler = FinanceDbHandler(session)
        
        if UPDATE_FINANCE_EXECUTOR in target_list:
            pl_updating_symbol_list = [symbol_tuple.symbol for symbol_tuple in financeDbHandler.find_symbols_of_not_necessary_pl_updating(JpSymbolHandler.JP_SYMBOL)]
            pl_updated_cnt = 0
            logger.info("start update pl data count = {0}".format(str(len(pl_updating_symbol_list))))
            for pl_data in financeHandler.get_pl_data(pl_updating_symbol_list, options.process_num):
                if len(pl_data) > 0:
                    pl_updated_cnt += len(pl_data)
                    logger.info("update pl data done {0}/{1}".format(str(pl_updated_cnt), str(len(pl_updating_symbol_list))))
                    financeDbHandler.upsert_symbol_finances(pl_data)
                    session.commit()
            logger.info("finish update pl data, {0}symbols".format(str(len(pl_updating_symbol_list))))
                
        technicalHandler = TechnicalHandler(logger, config.get("symbol", "symbol_for_rs_term"))
        technicalDbHandler = TechnicalDbHandler(session)
        
        if UPDATE_STOCK_EXECUTOR in target_list:
            stock_symbol_list = [symbol_tuple.symbol for symbol_tuple in technicalDbHandler.find_symbols_of_not_necessary_stock_updating(JpSymbolHandler.JP_SYMBOL, today)]
            stock_updated_cnt = 0
            logger.info("start update stock data, all symbol count = {}".format(str(len(stock_symbol_list))))
            for stock_data in technicalHandler.get_termly_stock_data(stock_symbol_list, options.process_num):
                if len(stock_data) > 0:
                    stock_updated_cnt += len(stock_data)
                    technicalDbHandler.upsert_symbol_stocks(stock_data)
                    session.commit()
                    logger.info("update stock data done {0}/{1}".format(str(stock_updated_cnt), str(len(stock_symbol_list))))
            
            logger.info("finish update stock data, {0}symbols".format(str(len(stock_symbol_list))))
        
        db.close_session()
    
    except Exception as e:
        session.rollback()
        db.close_session()
        logger.info(traceback.format_exc())
        
        mail_body_template = MailHandler.read_mail_body_template(os.path.join(app_dir, "mail", "can_slim_system_error_mail_format.txt"))
        mail_body = mail_body_template.format(
            date = today,
            app_name = app_home,
            error_msg = traceback.format_exc()
        )
        MailHandler.send_mail(credentials_config.get("mail", "to_address"), "CANSLIMシステムエラー通知", mail_body)
        
        sys.exit(1)
        

def get_db_connection(db_config, db_name):
    db = DbHandler().get_instance()
    db.set_session(db_config, db_name)
    return db


if __name__ == "__main__":
    logger.info("start can_slim_jp")
    main()
    logger.info("end can_slim_jp")
