import os,io
import zipfile
import shutil

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
            os.mkdir("./{}".format(SYMBOL))

        for year in range(START_YEAR,END_YEAR+1):
            dl(year=year, month=None, pair=SYMBOL, platform=P.GENERIC_ASCII, time_frame=term_mapping[TERM])

            file_prefix = "DAT_ASCII_{0}_{1}_{2}".format(SYMBOL.upper(), TERM, year)
            shutil.unpack_archive(file_prefix+".zip")
            shutil.copy(file_prefix+".csv", "./{0}/{1}".format(SYMBOL, file_prefix+".csv"))
            os.remove(file_prefix+".csv")
            os.remove(file_prefix+".txt")
            os.remove(file_prefix+".zip")
            
            print("{} done".format(year))
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        
if __name__ == "__main__":
    main()