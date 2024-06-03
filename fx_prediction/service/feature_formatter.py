import os
import pandas as pd
import pandas_datareader.data as web


class FeatureFormatter():
    def __init__(self, symbol, term, historical_dir):
        self._symbol = symbol
        self._term = term
        self._historical_dir = historical_dir
        
    def read_history_data_by_year(self, yyyy):
        historical_filename = f"{self._symbol}_{self._term}_{yyyy}.csv"
        df = pd.read_csv(os.path.join(self._historical_dir, historical_filename), sep="\t")
        df["datetime"] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'])
        df = df.rename(columns={"<CLOSE>": "close", "<TICKVOL>": "volume", "<OPEN>": "open", "<LOW>": "low", "<HIGH>": "high"})
        df = df[["datetime", "close", "volume"]]
        return df
        
    def read_history_data(self, before_year, after_year):
        df = pd.DataFrame(columns=["datetime","close"])
        for yyyy in range(before_year, after_year+1):
            df_temp = self.read_history_data_by_year(yyyy)
            df = pd.concat([df, df_temp], ignore_index=True)
            
        df = df.sort_values(by="datetime")
        return df
    
    def get_ticker_history(self, ticker, start_date, end_date):
        df = web.DataReader([ticker],'fred',start='2000-01-01', end="2020-01-01")
        return df[ticker]
    
    def set_history_diff(self, df, mh_term_list):
        column_list = []
        for term in mh_term_list:
            df[f"mh_{term}"] = self._calc_growth_rate(df["close"], df["close"].shift(term))
            column_list.append(f"mh_{term}")
        return df, column_list
    
    def set_moving_average_indicators(self, df, ma_term_list):
        column_list = []
        for term in ma_term_list:
            df[f"ma_{term}"] = df["close"].rolling(window=term).mean()
            # column_list.append(f"ma_{term}")
            
            df[f"ma_close_{term}"] = self._calc_growth_rate(df["close"], df[f"ma_{term}"])
            df[f"ma_diff_{term}"] = self._calc_growth_rate(df[f"ma_{term}"], df[f"ma_{term}"].shift(term))
            column_list.append(f"ma_close_{term}")
            column_list.append(f"ma_diff_{term}")
            
        return df, column_list
            
    def set_macd_indicators(self, df, short_window_list, long_window_list, signal_window_list):
        column_list = []
        for i in range(len(short_window_list)):
            short_window = short_window_list[i]
            long_window = long_window_list[i]
            signal_window = signal_window_list[i]
            
            short_ema = df["close"].ewm(span=short_window, adjust=False).mean()
            long_ema = df["close"].ewm(span=long_window, adjust=False).mean()
            
            df[f"macd_{short_window}_{long_window}_{signal_window}"] = short_ema - long_ema
            df[f"signal_line_{short_window}_{long_window}_{signal_window}"] = df[f"macd_{short_window}_{long_window}_{signal_window}"].ewm(span=signal_window, adjust=False).mean()
            column_list.append(f"macd_{short_window}_{long_window}_{signal_window}")
            column_list.append(f"signal_line_{short_window}_{long_window}_{signal_window}")
            
            ## MACDとMACDシグナルとの価格差
            df[f"macd_signal_diff_{short_window}_{long_window}_{signal_window}"] = self._calc_growth_rate(df[f"macd_{short_window}_{long_window}_{signal_window}"], df[f"signal_line_{short_window}_{long_window}_{signal_window}"])
            column_list.append(f"macd_signal_diff_{short_window}_{long_window}_{signal_window}")

            ## MACDと終値との価格差
            df[f"macd_close_diff_{short_window}_{long_window}_{signal_window}"] = self._calc_growth_rate(df["close"], df[f"macd_{short_window}_{long_window}_{signal_window}"])
            column_list.append(f"macd_close_diff_{short_window}_{long_window}_{signal_window}")

            ## MACDシグナルと終値との価格差
            df[f"signal_close_diff_{short_window}_{long_window}_{signal_window}"] = self._calc_growth_rate(df["close"], df[f"signal_line_{short_window}_{long_window}_{signal_window}"])
            column_list.append(f"signal_close_diff_{short_window}_{long_window}_{signal_window}")
            
        return df, column_list
        
    
    def set_bb_indicators(self, df, bb_term_list, bb_sigma_list):
        column_list = []
        for term in bb_term_list:
            for sigma in bb_sigma_list:
                # 上部バンドと下部バンドの計算
                std_dev = df["close"].rolling(window=term).std()
                df[f"upper_bb_{term}_{sigma}"] = df[f"ma_{term}"] + sigma * std_dev
                df[f"lower_bb_{term}_{sigma}"] = df[f"ma_{term}"] - sigma * std_dev
                df[f"upper_bb_close_{term}_{sigma}"] = self._calc_growth_rate(df["close"], df[f"upper_bb_{term}_{sigma}"])
                df[f"lower_bb_close_{term}_{sigma}"] = self._calc_growth_rate(df["close"], df[f"lower_bb_{term}_{sigma}"])
                
                column_list.append(f"upper_bb_{term}_{sigma}")
                column_list.append(f"lower_bb_{term}_{sigma}")
                column_list.append(f"upper_bb_close_{term}_{sigma}")
                column_list.append(f"lower_bb_close_{term}_{sigma}")
                
        return df, column_list
    
    def set_stochastics_indicators(self, df, stochastics_period_list, stochastics_ma_list):
        column_list = []
        for i in range(len(stochastics_period_list)):
            period = stochastics_period_list[i]
            ma_window = stochastics_ma_list[i]
            # %Kの計算
            df[f"stochastics_k_{period}"] = ((df["close"] - df["close"].rolling(window=period).min()) / 
                        (df["close"].rolling(window=period).max() - df["close"].rolling(window=period).min())) * 100

            column_list.append(f"stochastics_k_{period}")

            # %Dの計算
            df[f"stochastics_d_{period}_{ma_window}"] = df[f"stochastics_k_{period}"].rolling(window=ma_window).mean()
            column_list.append(f"stochastics_d_{period}_{ma_window}")
            df[f"stochastics_slow_d_{period}_{ma_window}"] = df[f"stochastics_d_{period}_{ma_window}"].rolling(window=ma_window).mean()
            column_list.append(f"stochastics_slow_d_{period}_{ma_window}")
            
        return df, column_list
    
    
    def _calc_growth_rate(self, target, pre):
        return round((target - pre) / pre * 100, 10)
        # return target - pre

