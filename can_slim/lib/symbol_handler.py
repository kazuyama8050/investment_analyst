import pandas as pd
import os,sys
import numpy as np

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
from date_format import DateFormat

class SymbolHandler():
    def __init__(self, config, default_report_date):
        self.config = config
        self._default_report_date = default_report_date
        self.symbol_list_filepath = os.path.join(app_dir, self.config.get("dataset", "usa_symbol_list_path"))
        
    def get_all_symbols_nyse(self):
        others_list = self.config.get("input", "usa_other_symbol_list_url")
        other = pd.read_csv(others_list, sep='|')
        #NYSEかつTest IssueでないかつETFでないものを取得する
        company_nyse = other[other['Exchange']=='N']
        company_nyse = other[other['Test Issue']=='N']
        company_nyse = company_nyse[company_nyse["ETF"] == "N"][['ACT Symbol', 'Security Name']]
        company_nyse = company_nyse.dropna()
        #indexはリセットする
        company_nyse = company_nyse.reset_index(drop=True)
        #ACT Symbol -> Symbol
        company_nyse = company_nyse.rename(columns={'ACT Symbol':'symbol', "Security Name": "name"})

        return company_nyse

    def get_all_symbols_nasdaq(self):
        nasdaq_list = self.config.get("input", "usa_nasdaq_symbol_list_url")
        nasdaq = pd.read_csv(nasdaq_list, sep='|')
        #StatusがNormalのものだけを取得する
        nasdaq_normal = nasdaq[nasdaq['Financial Status']=='N']
        #Test issueでないものを選択する
        nasdaq_normal = nasdaq_normal[nasdaq_normal['Test Issue']=='N']
        #ETFかどうかで判別
        company_nasdaq = nasdaq_normal[nasdaq_normal['ETF']=='N'][['Symbol', 'Security Name']]
        company_nasdaq = company_nasdaq.dropna()
        #indexはリセットする
        company_nasdaq = company_nasdaq.reset_index(drop=True)
        company_nasdaq = company_nasdaq.rename(columns={"Symbol": "symbol", "Security Name": "name"})

        return company_nasdaq

    def get_all_company_symbol(self, get_flag = False):
        if get_flag is False and os.path.exists(self.symbol_list_filepath):
            df = pd.read_csv(self.symbol_list_filepath)
            df["latestClosingDate"] = df["latestClosingDate"].apply(lambda x: DateFormat.string_to_date_format(x) if x is not np.nan else self._default_report_date)
            df = df.set_index("symbol", drop=False)
            return df, False
        
        nyse_companies = self.get_all_symbols_nyse()
        nasdaq_companies = self.get_all_symbols_nasdaq()

        nyse_companies["market"] = "NYSE"
        nasdaq_companies["market"] = "NASDAQ"

        merged_df = pd.concat([nyse_companies, nasdaq_companies], ignore_index=True, sort=False)
        merged_df["latestClosingDate"] = self._default_report_date
        merged_df = merged_df.loc[(merged_df["symbol"].str.contains('\.|\$') == False)]
        merged_df = merged_df.set_index("symbol", drop=False)
        return merged_df, True
    
    def write_symbol_list(self, df):
        df.to_csv(self.symbol_list_filepath, index=False)