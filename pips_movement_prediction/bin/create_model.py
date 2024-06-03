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
from light_gbm import LightGbm
from neural_network import NeuralNetwork

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
    parser.add_argument("-d", "--deviation", dest="deviation", action="store", help="deviation", default=1, type=int)
    return parser.parse_args()

options = get_options()

SYMBOL = options.symbol
TRAIN_DATA_TERM = options.term
BASE_PIPS = options.base_pips
TRAIN_DATA_START_YEAR = options.from_year
TRAIN_DATA_END_YEAR = options.until_year
SCRIPT_MODE = options.script_mode
DEVIATION = options.deviation

model_types = {
    "decision_tree": "決定木",
    "random_forest": "ランダムフォレスト",
    "light_gbm": "LightGBM",
    "neural_network": "ニューラルネットワーク",
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
        # featureFormatter.get_ticker_history("DGS10", "2010-01-01", "2023-02-01")
        # sys.exit()
        history_df = featureFormatter.read_history_data(TRAIN_DATA_START_YEAR, TRAIN_DATA_END_YEAR)
        logger.info("Read Historical Data From {0} To {1} Done. size: {2}".format(TRAIN_DATA_START_YEAR, TRAIN_DATA_END_YEAR, len(history_df)))
        
        """
        特徴量を算出
        """
        history_df, feature_columns = _set_feature_data(featureFormatter, history_df)
        
        """
        特徴量を選出
        """
        objective_column = "movement"

        history_df = history_df.dropna()
        logger.info("Create Feature Data All Size: {}".format(len(history_df)))
        ## 二値分類のデータ数を統一する
        min_size = min(len(history_df.loc[history_df[objective_column] == 1]), len(history_df.loc[history_df[objective_column] == 0]))
        history_df_a = history_df[history_df[objective_column] == 1].sample(n=min_size, random_state=42)
        history_df_b = history_df[history_df[objective_column] == 0].sample(n=min_size, random_state=42)
        history_df = pd.concat([history_df_a, history_df_b]).reset_index(drop=True)
        history_df = history_df.sample(frac=1, random_state=0)
        logger.info("Create Feature Data Done. upper_pips_movement_size: {0}, lower_pips_movement_size: {1}".format(len(history_df.loc[history_df[objective_column] == 1]), len(history_df.loc[history_df[objective_column] == 0])))
        
        X = history_df[feature_columns]
        Y = history_df[[objective_column]]
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.3, random_state=42)
        
        logger.info("Model Traning Start.")
        if MODEL_TYPE == "decision_tree":
            model = DecisionTree(logger, os.path.join(app_dir, config.get("model", "decision_tree_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=str(BASE_PIPS).replace(".", ""))))
        elif MODEL_TYPE == "random_forest":
            model = RandomForest(logger, os.path.join(app_dir, config.get("model", "random_forest_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=str(BASE_PIPS).replace(".", ""))))
        elif MODEL_TYPE == "light_gbm":
            model = LightGbm(logger, os.path.join(app_dir, config.get("model", "light_gbm_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=str(BASE_PIPS).replace(".", ""))))
        elif MODEL_TYPE == "neural_network":
            model = NeuralNetwork(logger, os.path.join(app_dir, config.get("model", "neural_network_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=str(BASE_PIPS).replace(".", ""))))
            
        if MODEL_TYPE == "light_gbm":
            X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, test_size=0.3, random_state=0)
            trained_model = model.train(X_train, X_val, y_train, y_val)
        else:
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
    history_df, feature_columns = _set_feature_data(featureFormatter, history_df)
    
    """
    特徴量を選出
    """
    objective_column = "movement"
    history_df = history_df.dropna()
    history_df.head(1000).to_csv("test.csv", index=False)
    logger.info("Create Feature Data All Size: {}".format(len(history_df)))
    history_df = history_df.sample(frac=1, random_state=0)
    logger.info("Create Feature Data Done. upper_pips_movement_size: {0}, lower_pips_movement_size: {1}".format(len(history_df.loc[history_df[objective_column] == 1]), len(history_df.loc[history_df[objective_column] == 0])))
    
    X = history_df[feature_columns]
    Y = history_df[[objective_column]]
    
    if MODEL_TYPE == "decision_tree":
        model = DecisionTree(logger, os.path.join(app_dir, config.get("model", "decision_tree_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=str(BASE_PIPS).replace(".", ""))))
    elif MODEL_TYPE == "random_forest":
        model = RandomForest(logger, os.path.join(app_dir, config.get("model", "random_forest_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=str(BASE_PIPS).replace(".", ""))))
    elif MODEL_TYPE == "light_gbm":
        model = LightGbm(logger, os.path.join(app_dir, config.get("model", "light_gbm_model_filepath").format(symbol=SYMBOL, term=TRAIN_DATA_TERM, base_pips=str(BASE_PIPS).replace(".", ""))))
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
    
    history_df = featureFormatter.set_pips_moving_direction(history_df, BASE_PIPS, DEVIATION)
    logger.info("Set Pips Moving Direction Done.")
    
    column_list.append("volume")
    return history_df, sorted(column_list)

if __name__ == "__main__":
    logger.info("start create_model")
    if SCRIPT_MODE in [1,2]:
        main()
    elif SCRIPT_MODE == 3:
        only_prediction()
    logger.info("end create_model")