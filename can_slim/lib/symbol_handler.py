import os,sys
import pandas as pd

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

class SymbolHandler():
    def __init__(self, symbol_list_filepath):
        self.symbol_list_filepath = symbol_list_filepath
        
    def get_all_symbols(self):
        df = pd.read_csv(self.symbol_list_filepath)
        return df["symbol"].unique().tolist()
    
    def read_all_symbol_infos(self):
        return pd.read_csv(self.symbol_list_filepath)

    def update_symbol_list_csv(self, df):
        df.to_csv(self.symbol_list_filepath, index=False)
        