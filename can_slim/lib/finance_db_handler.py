from sqlalchemy.sql import text

class FinanceDbHandler():
    FINANCE_VALID = 1
    FINANCE_INVALID = 0
    def __init__(self, db):
        self.db = db
        
    def find_symbols_of_not_necessary_pl_updating(self, country):
        sql = text(f'''
                    select ss.symbol from investment_analyst.symbols ss
                    where ss.country = '{country}' and ss.symbol not in (
                        select sf.symbol from investment_analyst.symbol_finances sf
                        where sf.latest_closing_date >= NOW() - INTERVAL 4 MONTH
                    )
            ''')
        return self.db.execute(sql).fetchall()
    
    def find_valid_finances(self, country):
        sql = text(f'''
                    select sf.symbol, sf.four_quarters_eps, sf.three_quarters_eps, sf.two_quarters_eps, sf.latest_quarter_eps, 
                    sf.four_quarters_revenue, sf.three_quarters_revenue, sf.two_quarters_revenue, sf.latest_quarter_revenue, 
                    sf.four_years_eps, sf.three_years_eps, sf.two_years_eps, sf.latest_year_eps, 
                    sf.latest_year_roe 
                    from investment_analyst.symbols ss
                    left join investment_analyst.symbol_finances sf
                    on sf.symbol = ss.symbol and ss.country = '{country}'
                    where sf.is_valid = {self.FINANCE_VALID}
            ''')
        return self.db.execute(sql).fetchall()
    
    def upsert_symbol_finances(self, finance_list):
        sql = text('''
                insert into investment_analyst.symbol_finances (
                    symbol, latest_closing_date, is_valid, 
                    four_quarters_eps, three_quarters_eps, two_quarters_eps, latest_quarter_eps, 
                    four_quarters_revenue, three_quarters_revenue, two_quarters_revenue, latest_quarter_revenue, 
                    four_years_eps, three_years_eps, two_years_eps, latest_year_eps, 
                    latest_year_roe
                )
                values (
                    :symbol, :latest_closing_date, :is_valid, 
                    :four_quarters_eps, :three_quarters_eps, :two_quarters_eps, :latest_quarter_eps, 
                    :four_quarters_revenue, :three_quarters_revenue, :two_quarters_revenue, :latest_quarter_revenue, 
                    :four_years_eps, :three_years_eps, :two_years_eps, :latest_year_eps, 
                    :latest_year_roe
                )
                on duplicate key update
                    latest_closing_date = VALUES(latest_closing_date),
                    is_valid = VALUES(is_valid),
                    four_quarters_eps = VALUES(four_quarters_eps),
                    three_quarters_eps = VALUES(three_quarters_eps),
                    two_quarters_eps = VALUES(two_quarters_eps),
                    latest_quarter_eps = VALUES(latest_quarter_eps),
                    four_quarters_revenue = VALUES(four_quarters_revenue),
                    three_quarters_revenue = VALUES(three_quarters_revenue),
                    two_quarters_revenue = VALUES(two_quarters_revenue),
                    latest_quarter_revenue = VALUES(latest_quarter_revenue),
                    four_years_eps = VALUES(four_years_eps),
                    three_years_eps = VALUES(three_years_eps),
                    two_years_eps = VALUES(two_years_eps),
                    latest_year_eps = VALUES(latest_year_eps),
                    latest_year_roe = VALUES(latest_year_roe)
            ''')
        self.db.execute(sql, finance_list)