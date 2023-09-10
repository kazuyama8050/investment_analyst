import os,sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pandas_datareader.data as web
import yfinance as yf
import investpy
import traceback
import numpy as np
import pandas as pd

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
    def __init__(self, df, main_df_filepath):
        self.df = df
        self.main_df_filepath = main_df_filepath
        
    def set_necessary_pl_data(self):
        target_symbol = ""
        try:
            cnt=0
            for symbol in self.df["symbol"].unique():
                cnt+=1
                # if cnt < 2470: continue
                target_symbol = symbol
                target_df = self.get_target_df(symbol)
                if target_df is False: continue
                
                self.df.at[symbol, "is_valid"] = 0

                data = yf.Ticker(symbol)
                if len(data.quarterly_financials) == 0 or len(data.financials) == 0 or len(data.balance_sheet) == 0 or len(data.quarterly_balance_sheet) == 0:
                    print("not found. symbol={}".format(symbol))
                    continue

                if len(data.quarterly_financials.columns) < 4 or len(data.financials.columns) < 4 or len(data.balance_sheet.columns) < 4 or len(data.quarterly_balance_sheet) < 4:
                    print("not found enough data. symbol={}".format(symbol))
                    continue

                latest_closing_date = DateFormat.timestamp_to_date_format(data.quarterly_financials.columns[0])
                if target_df["latestClosingDate"] >= latest_closing_date: continue

                quarterly_financial_df = data.quarterly_financials.iloc[:, :4]  ## 直近四半期P/L
                quarterly_bs_df = data.quarterly_balance_sheet.iloc[:, :4]  ## 直近四半期B/S
                yearly_financial_df = data.financials.iloc[: ,:4]  ## 直近4年間P/L
                yearly_bs_df = data.balance_sheet.iloc[:, :4]  ## 直近4年間B/S
                
                self.df.at[symbol, "latestClosingDate"] = latest_closing_date
                
                ## 四半期EPS
                if self.set_quarter_eps(quarterly_financial_df, quarterly_bs_df, symbol) == False:
                    continue
                
                ## 四半期売上高
                if self.set_quarter_revenue(quarterly_financial_df, symbol) == False:
                    continue

                 ## 年間EPS
                if self.set_yearly_eps(yearly_financial_df, yearly_bs_df, symbol) == False:
                    continue
                
                ## 年間ROE
                if self.set_yearly_roe(yearly_financial_df, yearly_bs_df, symbol) == False:
                    continue
                
                self.df.at[symbol, "is_valid"] = 1
                
                if cnt % 100 == 0:
                    self.df.to_csv(self.main_df_filepath, index = False)      
                

        except Exception as e:
            print("Error symbol={0}, msg={1}".format(target_symbol, e))
            print(traceback.format_exc())

        return self.df
    
    def get_target_df(self, symbol):
        target_df = self.df.loc[self.df["symbol"] == symbol]
        if len(target_df) != 1:
            print("invalid symbol={}".format(symbol))
            return False

        target_df = target_df.iloc[0]

        if target_df["latestClosingDate"] >= three_month_ago:
            return False
        
        return target_df
    
    def set_quarter_eps(self, quarterly_financial_df, quarterly_bs_df, symbol):
        if "Net Income" not in quarterly_financial_df.index:
            print("not found enough quarterly net income data. symbol={}".format(symbol))
            return False
        
        quarterly_income = quarterly_financial_df.loc["Net Income"]  ## 純利益
        if quarterly_income.isna().any() or len(quarterly_income) < 4:
            print("not found enough quarterly net income data. symbol={}".format(symbol))
            return False
        
        if "Share Issued" not in quarterly_bs_df.index:
            print("not found enough quarterly share issue. symbol={}".format(symbol))
            return False
        
        quarterly_share_issue = quarterly_bs_df.loc["Share Issued"]  ## 発行済み株式数
        if quarterly_share_issue.isna().any() or len(quarterly_share_issue) < 4:
            print("not found enough quarterly share issue. symbol={}".format(symbol))
            return False
        
        self.df.at[symbol, "four_quarters_eps"] = self.calc_eps(quarterly_income[3], quarterly_share_issue[3])
        self.df.at[symbol, "three_quarters_eps"] = self.calc_eps(quarterly_income[2], quarterly_share_issue[2])
        self.df.at[symbol, "two_quarters_eps"] = self.calc_eps(quarterly_income[1], quarterly_share_issue[1])
        self.df.at[symbol, "latest_quarter_eps"] = self.calc_eps(quarterly_income[0], quarterly_share_issue[0])
        return True
    
    def set_yearly_eps(self, yearly_financial_df, yearly_bs_df, symbol):
        if "Net Income" not in yearly_financial_df.index:
            print("not found enough yearly income. symbol={}".format(symbol))
            return False
        
        yearly_income = yearly_financial_df.loc["Net Income"]  ## 純利益
        if yearly_income.isna().any() or len(yearly_income) < 4:
            print("not found enough yearly income. symbol={}".format(symbol))
            return False
        
        if "Share Issued" not in yearly_bs_df.index:
            print("not found enough yearly share issue. symbol={}".format(symbol))
            return False
        
        yearly_share_issue = yearly_bs_df.loc["Share Issued"]  ## 発行済み株式数
        if yearly_share_issue.isna().any() or len(yearly_share_issue) < 4:
            print("not found enough yearly share issue. symbol={}".format(symbol))
            return False

        self.df.at[symbol, "four_years_eps"] = self.calc_eps(yearly_income[3], yearly_share_issue[3])
        self.df.at[symbol, "three_years_eps"] = self.calc_eps(yearly_income[2], yearly_share_issue[2])
        self.df.at[symbol, "two_years_eps"] = self.calc_eps(yearly_income[1], yearly_share_issue[1])
        self.df.at[symbol, "latest_year_eps"] = self.calc_eps(yearly_income[0], yearly_share_issue[0])
        
        return True
    
    def set_quarter_revenue(self, quarterly_financial_df, symbol):
        if "Total Revenue" not in quarterly_financial_df.index:
            print("not found enough quarterly total revenue data. symbol={}".format(symbol))
            return False

        quarterly_revenue = quarterly_financial_df.loc["Total Revenue"]  ## 売上高
        if quarterly_revenue.isna().any() or len(quarterly_revenue) < 4:
            print("not found enough quarterly total revenue data. symbol={}".format(symbol))
            return False

        self.df.at[symbol, "four_quarters_revenue"] = int(quarterly_revenue[3])
        self.df.at[symbol, "three_quarters_revenue"] = int(quarterly_revenue[2])
        self.df.at[symbol, "two_quarters_revenue"] = int(quarterly_revenue[1])
        self.df.at[symbol, "latest_quarter_revenue"] = int(quarterly_revenue[0])
        
        return True
    
    def set_yearly_roe(self, yearly_financial_df, yearly_bs_df, symbol):
        if "Stockholders Equity" not in yearly_bs_df.index:
            print("not found enough yearly stockholder_equity. symbol={}".format(symbol))
            return False
        
        yearly_stockholder_equity = yearly_bs_df.loc["Stockholders Equity"]  ## 自己資本金額
        if np.isnan(yearly_stockholder_equity[0]):
            print("not found enough yearly stockholder_equity. symbol={}".format(symbol))
            return False
        
        if "Net Income" not in yearly_financial_df.index:
            print("not found enough yearly income. symbol={}".format(symbol))
            return False
        
        yearly_income = yearly_financial_df.loc["Net Income"]  ## 純利益
        if np.isnan(yearly_income[0]):
            print("not found enough yearly income. symbol={}".format(symbol))
            return False

        self.df.at[symbol, "latest_year_roe"] = self.calc_roe(yearly_income[0], yearly_stockholder_equity[0])
        
        return True
    
    def calc_eps(self, income, share_issue):
        if int(income) == 0 or int(share_issue) == 0:
            return np.nan
        return round(int(income) / int(share_issue), 2)
    
    def calc_roe(self, income, stockholder_equity):
        if int(income) == 0 or int(stockholder_equity) == 0:
            return np.nan
        return round(int(income) / int(stockholder_equity) * 100, 2)