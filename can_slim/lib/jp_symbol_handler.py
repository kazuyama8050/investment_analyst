import pandas as pd
import os,sys
import numpy as np
import requests
from sqlalchemy.sql import text

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
from date_format import DateFormat

class JpSymbolHandler():
    JP_SYMBOL = "JP"
    def __init__(self, config):
        self.config = config
        self.symbol_list_downloadpath = os.path.join(app_dir, self.config.get("input", "jp_symbol_list_downloadpath"))
        
    def download_symbol_list(self):
        symbol_list_endpoint = self.config.get("input", "jp_symbol_list_endpoint")
        r = requests.get(symbol_list_endpoint)
        with open(os.path.join(app_dir, self.symbol_list_downloadpath), 'wb') as output:
            output.write(r.content)

    def get_all_company_symbol(self):
        self.download_symbol_list()
        df = pd.read_excel(os.path.join(app_dir, self.symbol_list_downloadpath))
        df = df[["コード", "銘柄名", "市場・商品区分"]]
        df = df.dropna()
        df = df.rename(columns={"コード": "symbol", "銘柄名": "name", "市場・商品区分": "market"})
        df = df.loc[df["market"].str.contains("プライム|グロース|スタンダード") == True]
        df["symbol"] = df['symbol'].astype(str) + '.T'
        df["country"] = JpSymbolHandler.JP_SYMBOL
        return df.to_dict(orient='records')
    
    