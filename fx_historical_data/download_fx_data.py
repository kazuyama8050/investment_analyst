"""
FXデータダウンロードスクリプト
※ fx_historical_dataディレクトリから実行すること
"""

import os,io
import zipfile
import shutil
import pandas as pd

from histdata import download_hist_data as dl
from histdata.api import Platform as P, TimeFrame as TF

import sys,traceback

def main():
    try:
        args = sys.argv

        SYMBOL = args[1]
        TERM = args[2]
        START_YEAR = int(args[3])
        END_YEAR = int(args[4])

        term_mapping = {
            "M1": TF.ONE_MINUTE
        }

        if os.path.exists("./{}".format(SYMBOL)) is False:
            os.mkdir(SYMBOL)

        for year in range(START_YEAR,END_YEAR+1):
            dl(year=year, month=None, pair=SYMBOL, platform=P.GENERIC_ASCII, time_frame=term_mapping[TERM])

            file_prefix = "DAT_ASCII_{0}_{1}_{2}".format(SYMBOL.upper(), TERM, year)
            shutil.unpack_archive(file_prefix+".zip")
            df = pd.read_csv(file_prefix+".csv", header=None, names=["datetime", 'open', 'higher', "lower", "close", "volume"], sep=";")
            df.to_csv(os.path.join(SYMBOL, file_prefix+".csv"), index=False)
            os.remove(file_prefix+".csv")
            os.remove(file_prefix+".txt")
            os.remove(file_prefix+".zip")
            
            print("{} done".format(year))
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        
if __name__ == "__main__":
    main()
    # filepath = "usdjpy/DAT_ASCII_{0}_{1}_{2}.csv".format("USDJPY", "M1", 2015)
    # df = pd.read_csv(filepath, sep=";")
    # print(df)