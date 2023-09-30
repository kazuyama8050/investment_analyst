import os,sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pandas_datareader.data as web
import yfinance as yf
from yahoofinancials import YahooFinancials
import investpy
import traceback
import numpy as np
import pandas as pd
import concurrent.futures
import multiprocessing
import threading

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
sys.path.append(os.path.join(app_dir, "lib"))

from date_format import DateFormat

today = datetime.today().date()
three_month_ago = today - relativedelta(months=3)
six_month_ago = today - relativedelta(months=6)
nine_month_ago = today - relativedelta(months=9)
one_year_ago = today - relativedelta(months=12)

## 営業日前基準（keyはdfカラムに相当） レラティブストレングス用
rs_termly_dict = {
    "c": today,
    "c63": three_month_ago,
    "c126": six_month_ago,
    "c189": nine_month_ago,
    "c252": one_year_ago
}


class TechnicalHandler:
    def __init__(self, logger, symbol_for_rs_term):
        self.logger = logger
        self.new_rs_termly_dict = self.get_termly_sales_date(symbol_for_rs_term)
        
    def get_termly_stock_data(self, symbol_list, process_num=1):
        try:
            symbol_seg_list = []
            symbol_seg = []
            cnt = 0
            for symbol in symbol_list:
                symbol_seg.append(symbol)
                cnt += 1
                if cnt % 100 == 0:
                    symbol_seg_list.append(symbol_seg)
                    symbol_seg = []
                    
            symbol_seg_list.append(symbol_seg)
            symbol_seg = []
                        
            cnt = 0
            for symbols in symbol_seg_list:
                stock_close_data = self.download_stock_close_data(symbols, DateFormat.date_to_string_format(one_year_ago), DateFormat.date_to_string_format(today))
                results = []
                with concurrent.futures.ProcessPoolExecutor(max_workers=process_num) as executor:
                    while True:
                        futures = [executor.submit(self.set_stock_data_for_multi_process, symbol, stock_close_data) for symbol in symbols]
                        for future in concurrent.futures.as_completed(futures):
                            result = future.result()
                            cnt += 1
                            results.append(result)
                        
                        if len(symbols) <= len(results): break
                yield results
                
            yield results            
        except Exception as e:
            self.logger.info(traceback.format_exc())
            
    def set_stock_data_for_multi_process(self, symbol, close_stock_datas):
        ret_dict = {}
        try:
            ret_dict["symbol"] = symbol
            ret_dict = self.set_default_stock_data(ret_dict)
            if symbol not in close_stock_datas.keys():
                self.logger.info("warning! not found stock data, symbol={}".format(symbol))
                return ret_dict
            
            close_stock_data = close_stock_datas[symbol]
            
            if len(close_stock_data) == 0:
                self.logger.info("warning! not found enough stock data, symbol={}".format(symbol))
                return ret_dict
            
            for k,d in self.new_rs_termly_dict.items():
                if d not in close_stock_data.keys():
                    self.logger.info("warning! not found enough stock data, symbol={0}, date={1}".format(symbol, d))
                    return ret_dict
                        
            for k, v in self.new_rs_termly_dict.items():
                ret_dict = self.get_close_stock_data(ret_dict, close_stock_data, k, v)
            
            ret_dict["is_valid"] = 1
                
            return ret_dict
                
        except Exception as e:
            self.logger.info("Error symbol={0}, msg={1}".format(symbol, e))
            self.logger.info(traceback.format_exc())
            
    def set_default_stock_data(self, ret_dict):
        ret_dict["is_valid"] = 0
        ret_dict["c"] = 0.0
        ret_dict["c63"] = 0.0
        ret_dict["c126"] = 0.0
        ret_dict["c189"] = 0.0
        ret_dict["c252"] = 0.0
        return ret_dict
        
            
    def download_stock_close_data(self, symbols, before, after):
        yahoo_financials = YahooFinancials(symbols)
        stock_data = yahoo_financials.get_historical_price_data(before, after, "daily")
        stock_dict = {}
        for symbol,datas in stock_data.items():
            stock_dict[symbol] = {}
            if "prices" not in datas.keys(): continue
            for price_datas in datas["prices"]:
                if pd.isna(price_datas["adjclose"]) or int(price_datas["adjclose"]) <= 0: continue
                stock_dict[symbol][price_datas["formatted_date"]] = int(price_datas["adjclose"])
        return stock_dict
            
    
    def get_close_stock_data(self, ret_dict, close_stock_datas, key, target_date):
        if target_date not in close_stock_datas.keys():
            return ret_dict
        
        ret_dict[key] = close_stock_datas[target_date]
        return ret_dict
        
            
            
    def get_termly_sales_date(self, symbol):
        stock_dict = self.download_stock_close_data(symbol, DateFormat.date_to_string_format(one_year_ago), DateFormat.date_to_string_format(today))
        new_rs_termly_dict = {}
        for k, v in rs_termly_dict.items():
            if k == "c":
                new_rs_termly_dict[k] = self.get_nearly_latest_sales_date(v, stock_dict, symbol)
            else:
                new_rs_termly_dict[k] = self.get_nearly_sales_date(v, stock_dict, symbol)

        return new_rs_termly_dict
            
    def get_nearly_sales_date(self, default_date, stock_dict, symbol):
        for i in range(0,8):
            target_date = DateFormat.date_to_string_format(default_date + relativedelta(days=i))
            if target_date in stock_dict[symbol].keys():
                return target_date
            
        raise("error!, cannot get nearly sales date")
    
    def get_nearly_latest_sales_date(self, today, stock_dict, symbol):
        for i in range(0,8):
            target_date = DateFormat.date_to_string_format(today - relativedelta(days=i))
            if target_date in stock_dict[symbol].keys():
                return target_date
            
        raise("error!, cannot get nearly sales date")
            
            