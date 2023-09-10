
class CanslimLogicHandler():
    quarterly_eps_clear_rate = 40
    yearly_eps_clear_rate = 25
    quarterly_revenue_clear_rate = 25
    yearly_roe_clear_val = 17
    
    def __init__(self, finance_df, stock_df):
        self.finance_df = finance_df
        self.stock_df = stock_df
        
    def mainLogic(self):
        self.finance_df = self.finance_df.dropna()
        self.finance_df["quarterly_eps_clear_seg"] = self.finance_df.apply(lambda row: self.get_clear_quarterly_eps_seg(row), axis=1)
        self.finance_df["yearly_eps_clear_seg"] = self.finance_df.apply(lambda row: self.get_clear_yearly_eps_seg(row), axis=1)
        self.finance_df["quarterly_revenue_clear_seg"] = self.finance_df.apply(lambda row: self.get_clear_quarterly_revenue_seg(row), axis=1)
        return self.finance_df
    
    def relative_strength_logic(self):
        self.stock_df["c63"].fillna(0, inplace = True)
        self.stock_df["c126"].fillna(0, inplace = True)
        self.stock_df["c189"].fillna(0, inplace = True)
        self.stock_df["c252"].fillna(0, inplace = True)
        
        self.stock_df["rs_index"] = self.stock_df.apply(lambda row: self.calc_relative_strength_index(row), axis=1)
        rs_percentile_dict = self.get_relative_strength_percentile(self.stock_df)
        print(rs_percentile_dict)
        self.stock_df["rs"] = self.stock_df["rs_index"].apply(lambda x: self.calc_relative_strength(x, rs_percentile_dict))
        
        return self.stock_df
        
    def get_clear_quarterly_eps_seg(self, row):
        if self.calc_progress_rate(row["two_quarters_eps"], row["latest_quarter_eps"]) >= self.quarterly_eps_clear_rate:
            if self.calc_progress_rate(row["three_quarters_eps"], row["two_quarters_eps"]) >= self.quarterly_eps_clear_rate:
                if self.calc_progress_rate(row["four_quarters_eps"], row["three_quarters_eps"]) >= self.quarterly_eps_clear_rate:
                    return 3
                return 2
            return 1
        return 0
        
    def get_clear_yearly_eps_seg(self, row):
        if self.calc_progress_rate(row["two_years_eps"], row["latest_year_eps"]) >= self.yearly_eps_clear_rate:
            if self.calc_progress_rate(row["three_years_eps"], row["two_years_eps"]) >= self.yearly_eps_clear_rate:
                if self.calc_progress_rate(row["four_years_eps"], row["three_years_eps"]) >= self.yearly_eps_clear_rate:
                    return 3
                return 2
            return 1
        return 0
    
    def get_clear_quarterly_revenue_seg(self, row):
        if self.calc_progress_rate(row["two_quarters_revenue"], row["latest_quarter_revenue"] >= self.quarterly_revenue_clear_rate):
            if self.calc_progress_rate(row["three_quarters_revenue"], row["two_quarters_revenue"] >= self.quarterly_revenue_clear_rate):
                if self.calc_progress_rate(row["four_quarters_revenue"], row["three_quarters_revenue"] >= self.quarterly_revenue_clear_rate):
                    return 3
                return 2
            return 1
        return 0
    
    
    def calc_relative_strength_index(self, row):
        if row["c"] == 0 or row["c63"] == 0 or row["c126"] == 0 or row["c189"] == 0 or row["c252"] == 0:
            return 0
        
        c63 = (row["c"] - row["c63"]) / row["c63"] * 0.4
        c126 = (row["c"] - row["c126"]) / row["c126"] * 0.2
        c189 = (row["c"] - row["c189"]) / row["c189"] * 0.2
        c252 = (row["c"] - row["c252"]) / row["c252"] * 0.2
        
        return (c63 + c126 + c189 + c252) * 100
    
    def get_relative_strength_percentile(self, df):
        rs_percentile_dict = {}
        for i in range(1, 101):
            num = i * 0.01
            rs_percentile_dict[i] = df["rs_index"].quantile(num)
        
        return dict(sorted(rs_percentile_dict.items(), key=lambda x: x[0], reverse=True))
    
    def calc_relative_strength(self, rs_index, rs_percentile_dict):
        if rs_index == 0: return 1
        for k,v in rs_percentile_dict.items():
            if rs_index >= v:
                return int(k)
            
        return 1
            
        
    def calc_progress_rate(self, before, after):
        if before == 0: before=0.01
        return round((after - before) / before * 100, 2)