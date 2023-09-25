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
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
sys.path.append(os.path.join(app_dir, "lib"))

from batch_settings import BatchSettings
from db_handler import DbHandler
from date_format import DateFormat
from symbol_handler import SymbolHandler
from usa_symbol_handler import UsaSymbolHandler
from finance_handler import FinanceHandler
from technical_handler import TechnicalHandler

options = BatchSettings.get_options()

config = configparser.ConfigParser()
config.read(os.path.join(app_dir, "conf/can_slim_usa.conf"))
credentials_config = configparser.ConfigParser()
credentials_config.read(os.path.join(app_dir, "conf/credentials-" + options.env + ".conf"))

logger = BatchSettings.get_logger(app_dir, app_home)

today = datetime.today().date()
three_month_ago = today - relativedelta(months=3)
three_month_later = today + relativedelta(months=3)
default_report_date = DateFormat.string_to_date_format("1970-01-01")

def main():
    try:
        db = get_db_connection(credentials_config, "investment_analyst")
        session = db.get_session()
        
        usaSymbolHandler = UsaSymbolHandler(config)
        symbolHandler = SymbolHandler(session)
        symbol_info_list = usaSymbolHandler.get_all_company_symbol()
        symbolHandler.update_symbol_list(symbol_info_list)
        session.commit()

        financeHandler = FinanceHandler(logger)
        financeDbHandler = FinanceDbHandler(session)
        pl_updating_symbol_list = [symbol_tuple.symbol for symbol_tuple in financeDbHandler.find_symbols_of_not_necessary_pl_updating(UsaSymbolHandler.USA_SYMBOL, three_month_ago)]

        pl_updated_cnt = 0
        logger.info("symbol count = {0}".format(str(len(pl_updating_symbol_list))))
        for pl_data in financeHandler.get_pl_data(pl_updating_symbol_list):
            if len(pl_data) > 0:
                pl_updated_cnt += len(pl_data)
                logger.info("update pl data done {0}/{1}".format(str(pl_updated_cnt), str(len(pl_updating_symbol_list))))
                financeDbHandler.upsert_symbol_finances(pl_data)
                session.commit()
        logger.info("finish update pl data, {0}symbols".format(str(len(pl_updating_symbol_list))))
                
        technicalHandler = TechnicalHandler(logger, config.get("symbol", "symbol_for_rs_term"))
        technicalDbHandler = TechnicalDbHandler(session)
        stock_symbol_list = [symbol_tuple.symbol for symbol_tuple in technicalDbHandler.find_symbols_of_not_necessary_stock_updating(UsaSymbolHandler.USA_SYMBOL, yesterday)]
        
        stock_updated_cnt = 0
        logger.info("start get stock data, all symbol count = {}".format(str(len(stock_symbol_list))))
        for stock_data in technicalHandler.get_termly_stock_data(stock_symbol_list):
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
        raise("Error msg={}".format(e))
        logger.info(traceback.format_exc())


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
    logger.info("start can_slim_usa")
    main()
    logger.info("end can_slim_usa")

