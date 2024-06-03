import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow import keras
import os,io
from sklearn.model_selection import train_test_split

EPOCHS = 2
BATCH_SIZE = 2

class RecursiveLstm():
    def __init__(self, logger, model_path, objective_column_name, time_steps):
        self._logger = logger
        self._model_path = model_path
        self._objective_column_name = objective_column_name
        self._time_steps = time_steps
        
    def train(self, X_train, y_train, X_val, y_val):
        # ## バッチサイズ整数倍にする
        # X_train = X_train[len(X_train) % BATCH_SIZE:]
        # y_train = y_train[len(y_train) % BATCH_SIZE:]
        # X_test = X_test[len(X_test) % BATCH_SIZE:]
        # y_test = y_test[len(y_test) % BATCH_SIZE:]


        scaler = MinMaxScaler()
        X_train = scaler.fit_transform(X_train)
        y_train = scaler.fit_transform(y_train)
        X_val = scaler.fit_transform(X_val)
        y_val = scaler.fit_transform(y_val)
        
        model = Sequential()
        # model.add(LSTM(units=50, input_shape=(None, X_train.shape[1])))
        model.add(LSTM(units=64, activation='relu', input_shape=(self._time_steps, X_train.shape[2]), return_sequences=True))
        # model.add(LSTM(units=32, activation='relu'))
        model.add(Dense(units=1, activation='sigmoid'))
        # model.build(input_shape=(None, X_train.shape[1]))
        model.compile(optimizer='adam', loss='mean_squared_error')
        print(model.summary())
       
        
        
        model.fit(
            X_train,
            y_train,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE, 
            callbacks=[keras.callbacks.EarlyStopping(
                monitor='val_loss',
                min_delta=0,
                patience=20,
                verbose=1
            )],
            validation_data=(X_val, y_val))
        return model
    
    def df_to_array(self, dataset, time_steps):
        df_y = dataset[[self._objective_column_name]]
        df_X = dataset.drop(columns=[self._objective_column_name])
        data_X = df_X.values
        data_y = df_y.values
        X, y = [], []
        for i in range(len(data_X) - time_steps):
            X.append(data_X[i:(i + time_steps), :])  # 入力シーケンス
            y.append(data_y[i + time_steps, :])      # 出力ラベル
        X = np.array(X)
        y = np.array(y)
        return X, y
    
    def write_model(self, model):
        return 
        
    def load_model(self, model, X_test, y_test):
        return
    
    def prediction(self, model, X_test, y_test):
        predictions = model.predict(X_test)
        return