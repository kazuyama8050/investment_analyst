import pandas as pd
import numpy as np
import os,io,sys
import configparser
import traceback
from sklearn.model_selection import train_test_split
from argparse import ArgumentParser

current_script_path = os.path.abspath(__file__)
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

sys.path.append(os.path.join(project_dir, "lib"))
sys.path.append(os.path.join(app_dir, "service"))

from batch_settings import BatchSettings
from feature_formatter import FeatureFormatter
from recursive_lstm import RecursiveLstm

config = configparser.ConfigParser()
config.read(os.path.join(app_dir, "conf/fx_prediction.conf"))

logger = BatchSettings.get_logger(app_dir, app_home)

def get_options():
    usage = "usage: %prog (Argument-1) [options]"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-s", "--symbol", dest="symbol", action="store", help="symbol", default="USDJPY", type=str)
    parser.add_argument("-t", "--term", dest="term", action="store", help="term", default="M1", type=str)
    parser.add_argument("-p", "--base_pips", dest="base_pips", action="store", help="base_pips", default=0.2, type=float)
    parser.add_argument("-f", "--from_year", dest="from_year", action="store", help="from_year", required=True, type=int)
    parser.add_argument("-u", "--until_year", dest="until_year", action="store", help="until_year", required=True, type=int)
    parser.add_argument("-m", "--model_type", dest="model_type", action="store", help="model_type", default="recursive_lstm", type=str)
    parser.add_argument("-c", "--script_mode", dest="script_mode", action="store", help="script_mode", default=1, type=int)
    return parser.parse_args()

options = get_options()

SYMBOL = options.symbol
TRAIN_DATA_TERM = options.term
BASE_PIPS = options.base_pips
TRAIN_DATA_START_YEAR = options.from_year
TRAIN_DATA_END_YEAR = options.until_year
SCRIPT_MODE = options.script_mode

model_types = {
    "recursive_lstm": "LSTM再帰モデル"
}
MODEL_TYPE = options.model_type

MOVING_HISTORY_TERM_LIST = [25, 50, 75, 125, 150, 175, 200, 225, 250]
MOVING_AVERAGE_TERM_LIST = [25, 50, 75, 125, 150, 175, 200, 225, 250]
BB_TERM_LIST = [25, 50, 75, 125, 150, 175, 200, 225, 250]
BB_SIGMA_LIST = [1, 2, 3, 4]

MACD_SHORT_WINDOW_LIST = [12, 26, 50]
MACD_LONG_WINDOW_LIST = [26, 12, 200]
MACD_SIGNAL_WINDOW_LIST = [9, 9, 9]

STOCHASTICS_PERIOD_LIST = [5,9,14]
STOCHASTICS_MA_LIST = [3,3,3]  ## 一般的には3固定

def main():
    try:
        if options.model_type not in model_types.keys():
            raise Exception("invalid model type")
        
        featureFormatter = FeatureFormatter(
            SYMBOL, TRAIN_DATA_TERM, os.path.join(project_dir, config.get("history_data", "dirname").format(symbol=SYMBOL.lower())) 
        )

        history_df = featureFormatter.read_history_data(TRAIN_DATA_START_YEAR, TRAIN_DATA_END_YEAR)
        logger.info("Read Historical Data From {0} To {1} Done. size: {2}".format(TRAIN_DATA_START_YEAR, TRAIN_DATA_END_YEAR, len(history_df)))
        
        """
        特徴量を算出
        """
        history_df, feature_columns = _set_feature_data(featureFormatter, history_df)
        
        """
        特徴量を選出
        """
        objective_column = "close"

        history_df = history_df.dropna()
        logger.info("Create Feature Data All Size: {}".format(len(history_df)))
        
        X = history_df[feature_columns]
        Y = history_df[[objective_column]]
        
        logger.info("Model Traning Start.")
        if MODEL_TYPE == "recursive_lstm":
            time_steps = 15
            model = RecursiveLstm(logger, os.path.join(app_dir, config.get("model", "recursive_lstm_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM)), objective_column, time_steps)
            
            history_df.drop(columns=["datetime"], inplace=True)
            X, y = model.df_to_array(history_df, time_steps)  
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

        if MODEL_TYPE == "recursive_lstm":
            trained_model = model.train(X_train, y_train, X_val, y_val)
        logger.info("Model Traning Done.")
        logger.info("Prediction Start.")
        model.prediction(trained_model, X_test, y_test)
        
        if SCRIPT_MODE == 2:
            model.write_model(trained_model)
            logger.info("Write Trained Model")
            
        logger.info("Prediction Done.")
        
    except Exception as e:
        logger.info("Critical Error! so Force Shutdown")
        logger.info(traceback.print_exc())
        sys.exit(1)
    
def only_prediction():
    featureFormatter = FeatureFormatter(
        SYMBOL, TRAIN_DATA_TERM, os.path.join(project_dir, config.get("history_data", "dirname").format(symbol=SYMBOL.lower())) 
    )
    history_df = featureFormatter.read_history_data(TRAIN_DATA_START_YEAR, TRAIN_DATA_END_YEAR)
    logger.info("Read Historical Data From {0} To {1} Done. size: {2}".format(TRAIN_DATA_START_YEAR, TRAIN_DATA_END_YEAR, len(history_df)))
    
    """
    特徴量を算出
    """
    history_df, feature_columns = _set_feature_data(featureFormatter, history_df)
    
    """
    特徴量を選出
    """
    objective_column = "close"
    history_df = history_df.dropna()
    logger.info("Create Feature Data All Size: {}".format(len(history_df)))
    
    X = history_df[feature_columns]
    Y = history_df[[objective_column]]
    
    if MODEL_TYPE == "recursive_lstm":
        model = DecisionTree(logger, os.path.join(app_dir, config.get("model", "recursive_lstm_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM)))

    trained_model = model.load_model()
    logger.info("Model Load Done.")
    logger.info("Prediction Start.")
    model.prediction(trained_model, X, Y)
    logger.info("Prediction Done.")
        

def _set_feature_data(featureFormatter, history_df):
    column_list = []
    
    history_df, history_diff_columns = featureFormatter.set_history_diff(history_df, MOVING_HISTORY_TERM_LIST)
    column_list += history_diff_columns
    logger.info("Set History Diff Done.")
    
    history_df, ma_columns = featureFormatter.set_moving_average_indicators(history_df, MOVING_AVERAGE_TERM_LIST)
    column_list += ma_columns
    logger.info("Set Moving Average Indicators Done.")
    
    
    history_df, macd_columns = featureFormatter.set_macd_indicators(history_df, MACD_SHORT_WINDOW_LIST, MACD_LONG_WINDOW_LIST, MACD_SIGNAL_WINDOW_LIST)
    column_list += macd_columns
    logger.info("Set MACD Indicators Done.")
    
    # history_df, bb_columns = featureFormatter.set_bb_indicators(history_df, BB_TERM_LIST, BB_SIGMA_LIST)
    # column_list += bb_columns
    # logger.info("Set BB Indicators Done.")
    
    history_df, stochastics_columns = featureFormatter.set_stochastics_indicators(history_df, STOCHASTICS_PERIOD_LIST, STOCHASTICS_MA_LIST)
    column_list += stochastics_columns
    logger.info("Set Stochastics Indicators Done.")
    
    column_list.append("volume")
    return history_df, sorted(column_list)



if __name__ == "__main__":
    logger.info("start create_model")
    if SCRIPT_MODE in [1,2]:
        main()
    elif SCRIPT_MODE == 3:
        only_prediction()
    logger.info("end create_model")