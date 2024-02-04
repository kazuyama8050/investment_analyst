import os,io
import zipfile
import shutil

from histdata import download_hist_data as dl
from histdata.api import Platform as P, TimeFrame as TF

import sys
args = sys.argv

SYMBOL = args[1]
TERM = args[2]
START_YEAR = int(args[3])
END_YEAR = int(args[4])

term_mapping = {
    "M1": TF.ONE_MINUTE
}
for year in range(START_YEAR,END_YEAR+1):
    dl(year=year, month=None, pair=SYMBOL, platform=P.GENERIC_ASCII, time_frame=term_mapping[TERM])

    file_prefix = "DAT_ASCII_{0}_{1}_{2}".format(SYMBOL.upper(), TERM, year)
    shutil.unpack_archive(file_prefix+".zip")
    shutil.move(file_prefix+".csv", "./{}/".format(SYMBOL))
    os.remove(file_prefix+".txt")
    os.remove(file_prefix+".zip")