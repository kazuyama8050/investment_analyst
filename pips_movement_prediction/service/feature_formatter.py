import os
import pandas as pd
import talib

class FeatureFormatter():
    def __init__(self, symbol, term, historical_dir):
        self._symbol = symbol
        self._term = term
        self._historical_dir = historical_dir
        
    def read_history_data_by_year(self, yyyy):
        historical_filename = f"DAT_ASCII_{self._symbol}_{self._term}_{yyyy}.csv"
        df = pd.read_csv(os.path.join(self._historical_dir, historical_filename), header=None, names=["datetime", 'open', 'higher', "lower", "close", "volume"])
        df = df[["datetime", "close"]]
        return df
        
    def read_history_data(self, before_year, after_year):
        df = pd.DataFrame(columns=["datetime","close"])
        for yyyy in range(before_year, after_year):
            df_temp = self.read_history_data_by_year(yyyy)
            df = pd.concat([df, df_temp], ignore_index=True)
            
        df = df.sort_values(by="datetime")
        return df
    
    def set_history_diff(self, df, mh_term_list):
        for term in mh_term_list:
            df[f"mh_{term}"] = (df["close"] - df["close"].shift(term*(-1))) / df["close"].shift(term*(-1)) * 100
        return df
    
    def set_moving_average_indicators(self, df, ma_term_list):
        for term in ma_term_list:
            df[f"ma_{term}"] = df['close'].rolling(window=term).mean()
            df[f"ma_close_{term}"] = (df["close"] - df[f"ma_{term}"]) / df[f"ma_{term}"] * 100
            df[f"ma_diff_{term}"] = (df[f"ma_{term}"] - df[f"ma_{term}"].shift(term*(-1))) / df[f"ma_{term}"].shift(term*(-1)) * 100
            
        return df
            
    def set_macd_indicators(self, df, short_window_list, long_window_list, signal_window_list):
        for i in range(len(short_window_list)):
            short_window = short_window_list[i]
            long_window = long_window_list[i]
            signal_window = signal_window_list[i]
            df[f"macd_{short_window}_{long_window}_{signal_window}"], df[f"signal_line_{short_window}_{long_window}_{signal_window}"], _ = talib.MACD(df["close"], fastperiod=short_window, slowperiod=long_window, signalperiod=signal_window)
            
            ## MACDとMACDシグナルとの価格差
            df[f"macd_signal_diff_{short_window}_{long_window}_{signal_window}"] = df[f"macd_{short_window}_{long_window}_{signal_window}"] - df[f"signal_line_{short_window}_{long_window}_{signal_window}"]

            ## MACDと終値との価格差
            df[f"macd_close_diff_{short_window}_{long_window}_{signal_window}"] = df[f"macd_{short_window}_{long_window}_{signal_window}"] - df["close"]

            ## MACDシグナルと終値との価格差
            df[f"signal_close_diff_{short_window}_{long_window}_{signal_window}"] = df[f"signal_line_{short_window}_{long_window}_{signal_window}"] - df["close"]

        return df
    
    def set_bb_indicators(self, df, bb_term_list, bb_sigma_list):
        for term in bb_term_list:
            for sigma in bb_sigma_list:
                # 上部バンドと下部バンドの計算
                std_dev = df['close'].rolling(window=term).std()
                df[f"upper_bb_close_{term}_{sigma}"] = (df[f"ma_{term}"] + sigma * std_dev) - df["close"]
                df[f"lower_bb_close_{term}_{sigma}"] = (df[f"ma_{term}"] - sigma * std_dev) - df["close"]
                
        return df
    
    def set_pips_moving_direction(self, df, base_pips):
        df_list = df.to_dict(orient="records")
        for i in range(len(df_list)):
            target_price = df_list[i]["close"]
            if i % 100000 == 0:
                print("{0}/{1} done".format(i, len(df_list)))
            if i >= len(df_list):
                break
            for y in range(i+1, len(df_list)):
                comparison_price = df_list[y]["close"]
                if comparison_price - target_price >= base_pips:  ## pips以上価格が上昇した時
                    df_list[i]["movement"] = 1
                    break;
                if target_price - comparison_price >= base_pips:  ## pips以上価格が下落した時
                    df_list[i]["movement"] = 0
                    break;
                continue
        return pd.DataFrame(df_list)