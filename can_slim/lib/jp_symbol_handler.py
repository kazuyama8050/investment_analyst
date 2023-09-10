import pandas as pd
import os,sys
import numpy as np
import requests

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
from date_format import DateFormat

class JpSymbolHandler():
    def __init__(self, config, default_report_date):
        self.config = config
        self._default_report_date = default_report_date
        self.symbol_list_downloadpath = os.path.join(app_dir, self.config.get("input", "jp_symbol_list_downloadpath"))
        self.symbol_list_filepath = os.path.join(app_dir, self.config.get("dataset", "jp_symbol_list_path"))
        
    def download_symbol_list(self):
        symbol_list_endpoint = self.config.get("input", "jp_symbol_list_endpoint")
        r = requests.get(symbol_list_endpoint)
        with open(os.path.join(app_dir, self.symbol_list_downloadpath), 'wb') as output:
            output.write(r.content)

    def get_all_company_symbol(self, get_flag = False):
        if get_flag is False and os.path.exists(self.symbol_list_filepath):
            df = pd.read_csv(self.symbol_list_filepath)
            df["latestClosingDate"] = df["latestClosingDate"].apply(lambda x: DateFormat.string_to_date_format(x) if x is not np.nan else self._default_report_date)
            df = df.set_index("symbol", drop=False)
            return df, False
        
        self.download_symbol_list()
        df = pd.read_excel(os.path.join(app_dir, self.symbol_list_downloadpath))
        df = df[["コード", "銘柄名", "市場・商品区分"]]
        df = df.dropna()
        df = df.rename(columns={"コード": "symbol", "銘柄名": "name", "市場・商品区分": "market"})
        df = df.loc[df["market"].str.contains("プライム|グロース|スタンダード") == True]
        df["latestClosingDate"] = self._default_report_date
        df["symbol"] = df['symbol'].astype(str) + '.T'
        df = df.set_index("symbol", drop=False)
        return df, True
    
    def write_symbol_list(self, df):
        df.to_csv(self.symbol_list_filepath, index=False)