import logging,os,sys
from configparser import ConfigParser
from argparse import ArgumentParser
import datetime

class BatchSettings(object):
    @staticmethod
    def get_options():
        usage = "usage: %prog (Argument-1) [options]"
        parser = ArgumentParser(usage=usage)
        parser.add_argument("-E", "--env", dest="env", action="store", help="env", default="dev", type=str)
        return parser.parse_args()
    
    @staticmethod
    def get_logger(app_dir, app_name):
        log_format = logging.Formatter(fmt=None, datefmt=None, style='%')
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(log_format)
        logger.addHandler(stdout_handler)
        
        log_filename = app_name + datetime.datetime.today().strftime("%Y%m")
        file_handler = logging.FileHandler(os.path.join(app_dir, "log", log_filename + ".log"), "a+")
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
        return logger