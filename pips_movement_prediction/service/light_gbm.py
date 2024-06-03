import lightgbm as lgb
from sklearn import metrics
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from imblearn.under_sampling import RandomUnderSampler
import os,io
import joblib
import pandas as pd
import numpy as np

class LightGbm():
    def __init__(self, logger, model_path):
        self._logger = logger
        self._model_path = model_path
        
        
    def train(self, X_train, X_val, y_train, y_val):        
        rus = RandomUnderSampler(random_state=0, replacement=True)
        x_resampled, y_resampled = rus.fit_resample(X_train, y_train)
        
        lgb_train = lgb.Dataset(x_resampled, y_resampled)
        lgb_eval = lgb.Dataset(X_val, y_val)
        params = {
            "objective": "binary",
            # "learning_rate": 0.01
        }
        verbose_eval = 0 # この数字を1にすると学習時のスコア推移がコマンドライン表示される
        
        lgb_model = lgb.train(
            params, 
            lgb_train,
            valid_sets=[lgb_train, lgb_eval],
            num_boost_round=1000,  ## 最大学習サイクル
            callbacks=[
                lgb.early_stopping(stopping_rounds=20, verbose=True),
                lgb.log_evaluation(verbose_eval)
            ]
        )
        return lgb_model
        
    def write_model(self, lgb_model):
        lgb_model.save_model(self._model_path)
        
    def load_model(self):
        # 保存したモデルを読み込み
        return lgb.Booster(model_file=self._model_path)
        
    def prediction(self, lgb_model, X_test, y_test):
        # テストデータでの予測
        y_pred = lgb_model.predict(X_test, num_iteration=lgb_model.best_iteration)

        # モデルの評価
        accuracy = accuracy_score(y_test, (y_pred >= 0.5).astype(int))
        fpr, tpr, threshold = metrics.roc_curve(y_test, y_pred)
        auc = metrics.auc(fpr, tpr)
                
        classification_report_result = classification_report(y_test, (y_pred >= 0.5))

        self._logger.info("Accuracy:{}\n".format(accuracy))
        self._logger.info("Classification Report:{}\n".format(classification_report_result))

        # 特徴量の重要度を取得
        feature_importances = lgb_model.feature_importance()
        importance_df = pd.DataFrame({'Feature': X_test.columns, 'Importance': feature_importances})
        importance_df = importance_df.sort_values(by='Importance', ascending=False)
        self._logger.info("特徴量の重要度:\n")
        for index, row in importance_df.iterrows():
            self._logger.info("{0}: {1}".format(row["Feature"], row["Importance"]))
        
        
        df = X_test
        df["real"] = y_test
        df["pred"] = y_pred
        for i in range(0,10):
            min = round(i*0.1, 1)
            max = round((i+1)*0.1,1)
            range_df = df.loc[(df["pred"] >= min) & (df["pred"] < max)]
            if len(range_df) == 0: continue
            print("pred range: {0}-{1}, num_rate: {2}, buy_rate: {3}, sell_rate: {4}".format(
                min, max, 
                round(len(range_df) / len(df), 5),
                round(len(range_df.loc[range_df["real"] == 1.0]) / len(range_df), 5),
                round(len(range_df.loc[range_df["real"] == 0.0]) / len(range_df), 5)
            ))
            




