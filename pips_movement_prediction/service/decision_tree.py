from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import os,io
import joblib
import pandas as pd

class DecisionTree():
    def __init__(self, logger, model_path):
        self._logger = logger
        self._model_path = model_path
        
        
    def train(self, X_train, y_train):
        # 決定木モデルのトレーニング
        dt_model = DecisionTreeClassifier()
        dt_model.fit(X_train, y_train)
        return dt_model
        
    def write_model(self, dt_model):
        joblib.dump(dt_model, self._model_path)
        
    def load_model(self):
        # 保存したモデルを読み込み
        return joblib.load(self._model_path)
        
    def prediction(self, dt_model, X_test, y_test):
        # テストデータでの予測
        y_pred = dt_model.predict(X_test)

        # モデルの評価
        accuracy = accuracy_score(y_test, y_pred)
        classification_report_result = classification_report(y_test, y_pred)

        self._logger.info("Accuracy:{}\n".format(accuracy))
        self._logger.info("Classification Report:{}\n".format(classification_report_result))

        self._logger.info('confusion matrix = {}\n'.format(confusion_matrix(y_true=y_test, y_pred=y_pred)))
        self._logger.info('accuracy = {}\n'.format(accuracy_score(y_true=y_test, y_pred=y_pred)))
        self._logger.info('precision = {}\n'.format(precision_score(y_true=y_test, y_pred=y_pred)))
        self._logger.info('recall = {}\n'.format(recall_score(y_true=y_test, y_pred=y_pred)))
        self._logger.info('f1 score = {}\n'.format(f1_score(y_true=y_test, y_pred=y_pred)))


        # 特徴量の重要度を取得
        feature_importances = dt_model.feature_importances_
        self._logger.info(feature_importances)
        importance_df = pd.DataFrame({'Feature': X_test.columns, 'Importance': feature_importances})
        importance_df = importance_df.sort_values(by='Importance', ascending=False)
        self._logger.info("特徴量の重要度:\n")
        self._logger.info(importance_df)

        # テストデータでの予測確率を取得
        predicted_probabilities = dt_model.predict_proba(X_test)
        self._logger.info("予測確率:\n")
        self._logger.info(predicted_probabilities)



