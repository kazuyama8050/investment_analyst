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
from decision_tree import DecisionTree
from random_forest import RandomForest

config = configparser.ConfigParser()
config.read(os.path.join(app_dir, "conf/pips_movement_prediction.conf"))

logger = BatchSettings.get_logger(app_dir, app_home)

def get_options():
    usage = "usage: %prog (Argument-1) [options]"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-s", "--symbol", dest="symbol", action="store", help="symbol", default="USDJPY", type=str)
    parser.add_argument("-t", "--term", dest="term", action="store", help="term", default="M1", type=str)
    parser.add_argument("-p", "--base_pips", dest="base_pips", action="store", help="base_pips", default=0.2, type=float)
    parser.add_argument("-f", "--from_year", dest="from_year", action="store", help="from_year", required=True, type=int)
    parser.add_argument("-u", "--until_year", dest="until_year", action="store", help="until_year", required=True, type=int)
    parser.add_argument("-m", "--model_type", dest="model_type", action="store", help="model_type", default="decision_tree", type=str)
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
    "decision_tree": "決定木",
    "random_forest": "ランダムフォレスト"
}
MODEL_TYPE = options.model_type

MOVING_HISTORY_TERM_LIST = [10, 25, 50, 75, 125, 200]
MOVING_AVERAGE_TERM_LIST = [10, 25, 50, 75, 125, 200]
BB_TERM_LIST = [10, 25, 50, 75, 125, 200]
BB_SIGMA_LIST = [1, 2, 3, 4]

MACD_SHORT_WINDOW_LIST = [12, 26, 50]
MACD_LONG_WINDOW_LIST = [26, 12, 200]
MACD_SIGNAL_WINDOW_LIST = [9, 9, 9]

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
        history_df = _set_feature_data(featureFormatter, history_df)
        
        """
        特徴量を選出
        """
        train_columns = _get_train_columns()
        objective_column = "movement"

        history_df = history_df.dropna()
        logger.info("Create Feature Data Done. upper_pips_movement_size: {0}, lower_pips_movement_size: {1}".format(len(history_df.loc[history_df[objective_column] == 1]), len(history_df.loc[history_df[objective_column] == 0])))
        
        X = history_df[train_columns]
        Y = history_df[[objective_column]]
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
        
        logger.info("Model Traning Start.")
        if MODEL_TYPE == "decision_tree":
            model = DecisionTree(logger, os.path.join(app_dir, config.get("model", "decision_tree_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=BASE_PIPS)))
        elif MODEL_TYPE == "random_forest":
            model = RandomForest(logger, os.path.join(app_dir, config.get("model", "random_forest_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=BASE_PIPS)))
        trained_model = model.train(X_train, y_train)
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
    history_df = _set_feature_data(featureFormatter, history_df)
    
    """
    特徴量を選出
    """
    train_columns = _get_train_columns()
    objective_column = "movement"

    history_df = history_df.dropna()
    logger.info("Create Feature Data Done. upper_pips_movement_size: {0}, lower_pips_movement_size: {1}".format(len(history_df.loc[history_df[objective_column] == 1]), len(history_df.loc[history_df[objective_column] == 0])))
    
    X = history_df[train_columns]
    Y = history_df[[objective_column]]
    
    if MODEL_TYPE == "decision_tree":
        model = DecisionTree(logger, os.path.join(app_dir, config.get("model", "decision_tree_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=BASE_PIPS)))
    elif MODEL_TYPE == "random_forest":
        model = RandomForest(logger, os.path.join(app_dir, config.get("model", "random_forest_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=BASE_PIPS)))
    trained_model = model.load_model()
    logger.info("Model Load Done.")
    logger.info("Prediction Start.")
    model.prediction(trained_model, X, Y)
    logger.info("Prediction Done.")
        

def _set_feature_data(featureFormatter, history_df):
    history_df = featureFormatter.set_history_diff(history_df, MOVING_HISTORY_TERM_LIST)
    logger.info("Set History Diff Done.")
    
    history_df = featureFormatter.set_moving_average_indicators(history_df, MOVING_AVERAGE_TERM_LIST)
    logger.info("Set Moving Average Indicators Done.")
    
    
    history_df = featureFormatter.set_macd_indicators(history_df, MACD_SHORT_WINDOW_LIST, MACD_LONG_WINDOW_LIST, MACD_SIGNAL_WINDOW_LIST)
    logger.info("Set MACD Indicators Done.")
    
    history_df = featureFormatter.set_bb_indicators(history_df, BB_TERM_LIST, BB_SIGMA_LIST)
    logger.info("Set BB Indicators Done.")
    
    history_df = featureFormatter.set_pips_moving_direction(history_df, BASE_PIPS)
    logger.info("Set Pips Moving Direction Done.")
    
    return history_df

def _get_train_columns():
    train_columns = []
    ## 終値
    for term in MOVING_HISTORY_TERM_LIST:
        train_columns.append(f"mh_{term}")
    ## 移動平均
    for term in MOVING_AVERAGE_TERM_LIST:
        train_columns.append(f"ma_close_{term}")
        train_columns.append(f"ma_diff_{term}")
    ## MACD
    for i in range(len(MACD_SHORT_WINDOW_LIST)):
        short_win = MACD_SHORT_WINDOW_LIST[i]
        long_win = MACD_LONG_WINDOW_LIST[i]
        signal_win = MACD_SIGNAL_WINDOW_LIST[i]
        train_columns.append(f"macd_signal_diff_{short_win}_{long_win}_{signal_win}")
        train_columns.append(f"macd_close_diff_{short_win}_{long_win}_{signal_win}")
        train_columns.append(f"signal_close_diff_{short_win}_{long_win}_{signal_win}")
    ## BB
    for term in BB_TERM_LIST:
        for sigma in BB_SIGMA_LIST:
            train_columns.append(f"upper_bb_close_{term}_{sigma}")
            train_columns.append(f"lower_bb_close_{term}_{sigma}")
    return train_columns

if __name__ == "__main__":
    logger.info("start create_model")
    if SCRIPT_MODE in [1,2]:
        main()
    elif SCRIPT_MODE == 3:
        only_prediction()
    logger.info("end create_model")