import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras import optimizers
import keras
import os,io
import joblib

class NeuralNetwork():
    def __init__(self, logger, model_path):
        self._logger = logger
        self._model_path = model_path
        
        
    def train(self, X_train, y_train):
        # 特徴量の標準化
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        # ニューラルネットワークの構築
        nn_model = Sequential()  ## 直列に層を重ねるモデル
        
        """
        層の追加
        
        Dense()
            - 引数1: ノード数
            - activation: 活性化関数
                - 中間層には「relu」、出力層には「sigmoid」がよい？
            - kernel_initializer: 重み初期化手法
                - 活性化関数が「relu」の場合、「He」の初期値
                - 活性化関数が「sigmoid」の場合、「Xaviar」が基本
        """
        nn_model.add(Dense(128, activation='relu', kernel_initializer=keras.initializers.he_normal(seed=0), name="middle_layer1"))
        nn_model.add(Dense(128, activation='relu', kernel_initializer=keras.initializers.he_normal(seed=0), name="middle_layer2"))
        nn_model.add(Dense(1, activation='sigmoid', kernel_initializer=keras.initializers.glorot_uniform(seed=0), name="output_layer"))
        
        nn_model.build(input_shape=(None, 52))
        
        # モデルのコンパイル
        nn_model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        
        self._logger.info(nn_model.summary())

        """ 
        モデルの訓練
        epochs: 訓練データ学習の繰り返し数
        batch_size: 1度にモデルに与える訓練データの数を指定する
        """
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
        )
        nn_model.fit(X_train_scaled, y_train, epochs=2, batch_size=2, verbose=1, callbacks=early_stopping)
        return nn_model
        
    def write_model(self, nn_model):
        joblib.dump(nn_model, self._model_path)
        
    def load_model(self):
        # 保存したモデルを読み込み
        return joblib.load(self._model_path)
        
    def prediction(self, nn_model, X_test, y_test):
        # 特徴量の標準化
        scaler = StandardScaler()
        X_test_scaled = scaler.fit_transform(X_test)
        
        _, accuracy = nn_model.evaluate(X_test_scaled, y_test)
        print("正解率: {}".format(accuracy))


