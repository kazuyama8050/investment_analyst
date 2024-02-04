import pandas as pd
import numpy as np
import os,io,sys
import configparser
import traceback
from sklearn.model_selection import train_test_split

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

SYMBOL = "USDJPY"
TRAIN_DATA_TERM = "M1"
BASE_PIPS = 0.2
TRAIN_DATA_START_YEAR = 2015
TRAIN_DATA_END_YEAR = 2022

MOVING_HISTORY_TERM_LIST = [10, 25, 50, 75, 125, 200]
MOVING_AVERAGE_TERM_LIST = [10, 25, 50, 75, 125, 200]
BB_TERM_LIST = [10, 25, 50, 75, 125, 200]
BB_SIGMA_LIST = [1, 2, 3, 4]

MACD_SHORT_WINDOW_LIST = [12, 26, 50]
MACD_LONG_WINDOW_LIST = [26, 12, 200]
MACD_SIGNAL_WINDOW_LIST = [9, 9, 9]

def main():
    try:
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
        model = DecisionTree(logger, os.path.join(app_dir, config.get("model", "random_forest_model_filepath")))
        trained_model = model.train(X_train, y_train)
        logger.info("Model Traning Done.")
        logger.info("Prediction Start.")
        model.prediction(trained_model, X_test, y_test)
        model.write_model(trained_model)
        logger.info("Prediction Done.")
        
    except Exception as e:
        logger.info("Critical Error! so Force Shutdown")
        logger.info(traceback.print_exc())
        sys.exit(1)
    
def only_prediction(prediction_data_year):
    featureFormatter = FeatureFormatter(
        SYMBOL, TRAIN_DATA_TERM, os.path.join(project_dir, config.get("history_data", "dirname").format(symbol=SYMBOL.lower())) 
    )
    history_df = featureFormatter.read_history_data_by_year(prediction_data_year)
    logger.info("Read Historical Data Of {0} Done. size: {1}".format(prediction_data_year, len(history_df)))
    
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
    
    model = RandomForest(logger, os.path.join(app_dir, config.get("model", "random_forest_model_filepath")))
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
    # main()
    only_prediction(2023)
    logger.info("end create_model")