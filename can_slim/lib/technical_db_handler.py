from sqlalchemy.sql import text

class TechnicalDbHandler():
    STOCK_VALID = 1
    STOCK_INVALID = 0
    def __init__(self, db):
        self.db = db
        
    def find_symbols_of_not_necessary_stock_updating(self, country, target_date):
        sql = text(f'''
                select ss.symbol from investment_analyst.symbols ss
                where ss.country = '{country}' and ss.symbol not in (
                    select sss.symbol from investment_analyst.symbol_stocks sss
                    where sss.update_time >= '{target_date}'
                )
        ''')
        return self.db.execute(sql).fetchall()
    
    def find_valid_stocks(self, country):
        sql = text(f'''
                    select sss.symbol, sss.c, sss.c63, 
                    sss.c126, sss.c189, sss.c252
                    from investment_analyst.symbol_stocks sss
                    left join investment_analyst.symbols ss
                    on sss.symbol = ss.symbol and ss.country = '{country}'
                    where sss.is_valid = {self.STOCK_VALID}
            ''')
        return self.db.execute(sql).fetchall()
        
    def upsert_symbol_stocks(self, stock_list):
        sql = text('''
                    insert into investment_analyst.symbol_stocks (
                        symbol, is_valid, c, c63, c126, c189, c252
                    )
                    values (
                        :symbol, :is_valid, :c, :c63, :c126, :c189, :c252
                    )
                    on duplicate key update
                        is_valid = VALUES(is_valid),
                        c = VALUES(c),
                        c63 = VALUES(c63),
                        c126 = VALUES(c126),
                        c189 = VALUES(c189),
                        c252 = VALUES(c252)
            ''')
        self.db.execute(sql, stock_list)