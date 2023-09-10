import os,sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pandas_datareader.data as web
import yfinance as yf
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
    "c63": three_month_ago,
    "c126": six_month_ago,
    "c189": nine_month_ago,
    "c252": one_year_ago
}


class TechnicalHandler:
    def __init__(self, df, main_stock_df_filepath, symbol_for_rs_term):
        self.df = df
        self.main_stock_df_filepath = main_stock_df_filepath
        self.symbol_for_rs_term = symbol_for_rs_term
        self.new_rs_termly_dict = self.get_termly_sales_date(symbol_for_rs_term)
        
    def set_termly_stock_data(self):
        
        
        target_symbol = ""
        try:
            unique_symbol_list = list(self.df["symbol"].unique())
            
            unique_symbol_seg_list = []
            unique_symbol_seg_str = ""
            seg_cnt = 0
            for unique_symbol in unique_symbol_list:
                unique_symbol_seg_str = unique_symbol_seg_str + " " + unique_symbol
                seg_cnt += 1
                if seg_cnt >= 100:
                    unique_symbol_seg_list.append(unique_symbol_seg_str)
                    unique_symbol_seg_str = ""
                    seg_cnt = 0
                    
            unique_symbol_seg_list.append(unique_symbol_seg_str)
            unique_symbol_seg_str = ""
            seg_cnt = 0
                    
            cnt = 0
            for symbol_seg in unique_symbol_seg_list:
                cnt += 1
                stock_close_data = self.download_stock_close_data(symbol_seg)
                close_data_columns = list(stock_close_data.columns)
                for col in close_data_columns:
                    self.set_stock_data_for_multi_process(col, stock_close_data)
                    
                self.df.to_csv(self.main_stock_df_filepath, index = False)
                print("{0}/{1} finished".format(str(cnt*100), str(len(unique_symbol_list))))
            
                
            return self.df
                
        except Exception as e:
            print("Error symbol={0}, msg={1}".format(target_symbol, e))
            print(traceback.format_exc())
            
    def set_stock_data_for_multi_process(self, symbol, close_stock_datas):
        try:
            if symbol not in close_stock_datas.columns:
                print("warning! not found stock data, symbol={}".format(symbol))
                return False
            
            close_stock_data = close_stock_datas[symbol]
            
            # if "Adj Close" not in stock_data.columns:
            #     print("warning! not found 'Adj Close' column, symbol={}".format(symbol))
            #     return False
            
            # close_stock_data = stock_data["Adj Close"]
            if close_stock_data.isna().any():
                print("warning! not found enough stock data, symbol={}".format(symbol))
                return False
            
            self.df.at[symbol, "c"] = close_stock_data[-1]
            
            is_all_data = True
            for k, v in self.new_rs_termly_dict.items():
                if self.get_close_stock_data(symbol, close_stock_data, k, v) == False:
                    is_all_data = False
            
            if is_all_data == True:
                self.df.at[symbol, "is_valid"] = 1
            else:
                self.df.at[symbol, "is_valid"] = 0
                
            return True
                
        except Exception as e:
            print("Error symbol={0}, msg={1}".format(symbol, e))
            print(traceback.format_exc())
            
    def download_stock_close_data(self, symbol_seg):
        stock_data = yf.download(symbol_seg, start=DateFormat.date_to_string_format(one_year_ago))
        return stock_data["Adj Close"]
            
    
    def get_close_stock_data(self, symbol, close_stock_datas, df_key, target_date):
        if target_date not in close_stock_datas.index:
            self.df.at[symbol, df_key] = 0
            return False
        
        self.df.at[symbol, df_key] = close_stock_datas.loc[target_date]
        return True
        
            
            
    def get_termly_sales_date(self, symbol):
        stock_df = yf.download(symbol, start=DateFormat.date_to_string_format(one_year_ago))
        new_rs_termly_dict = {}
        for k, v in rs_termly_dict.items():
            new_rs_termly_dict[k] = self.get_nearly_sales_date(v, stock_df)

        return new_rs_termly_dict
            
    def get_nearly_sales_date(self, default_date, stock_df):
        for i in range(0,8):
            target_date = DateFormat.date_to_datetimeindex_format(default_date + relativedelta(days=i))
            if target_date in stock_df.index:
                return target_date
            
        raise("error!, cannot get nearly sales date")
            
            