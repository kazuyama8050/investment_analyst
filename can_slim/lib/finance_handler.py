import os,sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pandas_datareader.data as web
import yfinance as yf
import investpy
import traceback
import numpy as np
import pandas as pd
import multiprocessing
import concurrent.futures

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
sys.path.append(os.path.join(app_dir, "lib"))

from date_format import DateFormat

today = datetime.today().date()
three_month_ago = today - relativedelta(months=3)
three_month_later = today + relativedelta(months=3)


class FinanceHandler:
    REVENUE_SCALE = 1000000  ## 売上高は百万単位
    REVENUE_DECIMAL_SCALE = 0
    def __init__(self, logger):
        self.logger = logger
        self.default_report_date = DateFormat.string_to_date_format("1970-01-01")
        
    def get_pl_data(self, symbol_list):
        try:
            results = []
            cnt = 0
            with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
                while True:
                    futures = [executor.submit(self.set_necessary_pl_data_by_multi_process, symbol) for symbol in symbol_list]
                    for future in concurrent.futures.as_completed(futures):
                        cnt+=1
                        result = future.result()
                        results.append(result)
                        
                        if len(results) >= 2:
                            yield results
                            results = []
                        
                    if cnt >= len(symbol_list): break
                
            yield results            
        except Exception as e:
            self.logger.info(traceback.format_exc())
        
    def set_necessary_pl_data_by_multi_process(self, symbol):
        try:
            ret_data = {}
            ret_data["symbol"] = symbol
            ret_data["is_valid"] = 0
            ret_data = self.set_default_data(ret_data)
            
            data = yf.Ticker(symbol)
            if len(data.quarterly_financials) == 0 or len(data.financials) == 0 or len(data.balance_sheet) == 0 or len(data.quarterly_balance_sheet) == 0:
                self.logger.info("not found. symbol={}".format(symbol))
                return ret_data

            if len(data.quarterly_financials.columns) < 4 or len(data.financials.columns) < 4 or len(data.balance_sheet.columns) < 4 or len(data.quarterly_balance_sheet) < 4:
                self.logger.info("not found enough data. symbol={}".format(symbol))
                return ret_data
            
            latest_closing_date = DateFormat.timestamp_to_date_format(data.quarterly_financials.columns[0])
            ret_data["latest_closing_date"] = latest_closing_date

            quarterly_financial_df = data.quarterly_financials.iloc[:, :4]  ## 直近四半期P/L
            quarterly_bs_df = data.quarterly_balance_sheet.iloc[:, :4]  ## 直近四半期B/S
            yearly_financial_df = data.financials.iloc[: ,:4]  ## 直近4年間P/L
            yearly_bs_df = data.balance_sheet.iloc[:, :4]  ## 直近4年間B/S
            
            ## 四半期EPS
            ret_data, is_valid = self.set_quarter_eps(ret_data, quarterly_financial_df, quarterly_bs_df, symbol)
            if is_valid == False: return ret_data
            
            ## 四半期売上高
            ret_data, is_valid = self.set_quarter_revenue(ret_data, quarterly_financial_df, symbol)
            if is_valid == False: return ret_data

            ## 年間EPS
            ret_data, is_valid = self.set_yearly_eps(ret_data, yearly_financial_df, yearly_bs_df, symbol)
            if is_valid == False: return ret_data
            
            ## 年間ROE
            ret_data, is_valid = self.set_yearly_roe(ret_data, yearly_financial_df, yearly_bs_df, symbol)
            if is_valid == False: return ret_data
            
            ret_data["is_valid"] = 1
            return ret_data
            
        except Exception as e:
            self.logger.info("Error symbol={0}, msg={1}".format(target_symbol, e))
            self.logger.info(traceback.format_exc())                    
    
    
    def set_default_data(self, ret_data):
        ret_data["latest_closing_date"] = self.default_report_date
        ret_data["four_quarters_eps"] = 0.0
        ret_data["three_quarters_eps"] = 0.0
        ret_data["two_quarters_eps"] = 0.0
        ret_data["latest_quarter_eps"] = 0.0
        ret_data["four_quarters_revenue"] = 0
        ret_data["three_quarters_revenue"] = 0
        ret_data["two_quarters_revenue"] = 0
        ret_data["latest_quarter_revenue"] = 0
        ret_data["four_years_eps"] = 0.0
        ret_data["three_years_eps"] = 0.0
        ret_data["two_years_eps"] = 0.0
        ret_data["latest_year_eps"] = 0.0
        ret_data["latest_year_roe"] = 0.0
        
        return ret_data
    
    
    def set_quarter_eps(self, ret_dict, quarterly_financial_df, quarterly_bs_df, symbol):
        if "Net Income" not in quarterly_financial_df.index:
            self.logger.info("not found enough quarterly net income data. symbol={}".format(symbol))
            return ret_dict, False
        
        quarterly_income = quarterly_financial_df.loc["Net Income"]  ## 純利益
        if quarterly_income.isna().any() or len(quarterly_income) < 4:
            self.logger.info("not found enough quarterly net income data. symbol={}".format(symbol))
            return ret_dict, False
        
        if "Share Issued" not in quarterly_bs_df.index:
            self.logger.info("not found enough quarterly share issue. symbol={}".format(symbol))
            return ret_dict, False
        
        quarterly_share_issue = quarterly_bs_df.loc["Share Issued"]  ## 発行済み株式数
        if quarterly_share_issue.isna().any() or len(quarterly_share_issue) < 4:
            self.logger.info("not found enough quarterly share issue. symbol={}".format(symbol))
            return ret_dict, False
        
        ret_dict["four_quarters_eps"] = self.calc_eps(quarterly_income.iloc[3], quarterly_share_issue.iloc[3])
        ret_dict["three_quarters_eps"] = self.calc_eps(quarterly_income.iloc[2], quarterly_share_issue.iloc[2])
        ret_dict["two_quarters_eps"] = self.calc_eps(quarterly_income.iloc[1], quarterly_share_issue.iloc[1])
        ret_dict["latest_quarter_eps"] = self.calc_eps(quarterly_income.iloc[0], quarterly_share_issue.iloc[0])
        return ret_dict, True
    
    def set_yearly_eps(self, ret_dict, yearly_financial_df, yearly_bs_df, symbol):
        if "Net Income" not in yearly_financial_df.index:
            self.logger.info("not found enough yearly income. symbol={}".format(symbol))
            return ret_dict, False
        
        yearly_income = yearly_financial_df.loc["Net Income"]  ## 純利益
        if yearly_income.isna().any() or len(yearly_income) < 4:
            self.logger.info("not found enough yearly income. symbol={}".format(symbol))
            return ret_dict, False
        
        if "Share Issued" not in yearly_bs_df.index:
            self.logger.info("not found enough yearly share issue. symbol={}".format(symbol))
            return ret_dict, False
        
        yearly_share_issue = yearly_bs_df.loc["Share Issued"]  ## 発行済み株式数
        if yearly_share_issue.isna().any() or len(yearly_share_issue) < 4:
            self.logger.info("not found enough yearly share issue. symbol={}".format(symbol))
            return ret_dict, False

        ret_dict["four_years_eps"] = self.calc_eps(yearly_income.iloc[3], yearly_share_issue.iloc[3])
        ret_dict["three_years_eps"] = self.calc_eps(yearly_income.iloc[2], yearly_share_issue.iloc[2])
        ret_dict["two_years_eps"] = self.calc_eps(yearly_income.iloc[1], yearly_share_issue.iloc[1])
        ret_dict["latest_year_eps"] = self.calc_eps(yearly_income.iloc[0], yearly_share_issue.iloc[0])
        
        return ret_dict, True
    
    def set_quarter_revenue(self, ret_dict, quarterly_financial_df, symbol):
        if "Total Revenue" not in quarterly_financial_df.index:
            self.logger.info("not found enough quarterly total revenue data. symbol={}".format(symbol))
            return ret_dict, False

        quarterly_revenue = quarterly_financial_df.loc["Total Revenue"]  ## 売上高
        if quarterly_revenue.isna().any() or len(quarterly_revenue) < 4:
            self.logger.info("not found enough quarterly total revenue data. symbol={}".format(symbol))
            return ret_dict, False

        ret_dict["four_quarters_revenue"] = self.round_unsigned_int(quarterly_revenue.iloc[3], self.REVENUE_SCALE, self.REVENUE_DECIMAL_SCALE)
        ret_dict["three_quarters_revenue"] = self.round_unsigned_int(quarterly_revenue.iloc[2], self.REVENUE_SCALE, self.REVENUE_DECIMAL_SCALE)
        ret_dict["two_quarters_revenue"] = self.round_unsigned_int(quarterly_revenue.iloc[1], self.REVENUE_SCALE, self.REVENUE_DECIMAL_SCALE)
        ret_dict["latest_quarter_revenue"] = self.round_unsigned_int(quarterly_revenue.iloc[0], self.REVENUE_SCALE, self.REVENUE_DECIMAL_SCALE)
        
        return ret_dict, True
    
    def set_yearly_roe(self, ret_dict, yearly_financial_df, yearly_bs_df, symbol):
        if "Stockholders Equity" not in yearly_bs_df.index:
            self.logger.info("not found enough yearly stockholder_equity. symbol={}".format(symbol))
            return False
        
        yearly_stockholder_equity = yearly_bs_df.loc["Stockholders Equity"]  ## 自己資本金額
        if np.isnan(yearly_stockholder_equity.iloc[0]):
            self.logger.info("not found enough yearly stockholder_equity. symbol={}".format(symbol))
            return ret_dict, False
        
        if "Net Income" not in yearly_financial_df.index:
            self.logger.info("not found enough yearly income. symbol={}".format(symbol))
            return ret_dict, False
        
        yearly_income = yearly_financial_df.loc["Net Income"]  ## 純利益
        if np.isnan(yearly_income.iloc[0]):
            self.logger.info("not found enough yearly income. symbol={}".format(symbol))
            return ret_dict, False

        ret_dict["latest_year_roe"] = self.calc_roe(yearly_income.iloc[0], yearly_stockholder_equity.iloc[0])
        
        return ret_dict, True
    
    def round_unsigned_int(self, num, scale, decimal_scale):
        if num < 0: return 0
        return round(int(num) / scale, decimal_scale)
    
    def calc_eps(self, income, share_issue):
        if int(income) == 0 or int(share_issue) == 0:
            return 0
        return round(int(income) / int(share_issue), 2)
    
    def calc_roe(self, income, stockholder_equity):
        if int(income) == 0 or int(stockholder_equity) == 0:
            return 0
        return round(int(income) / int(stockholder_equity) * 100, 2)