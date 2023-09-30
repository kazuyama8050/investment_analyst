import os,sys
from sqlalchemy.sql import text

current_script_path = os.path.abspath(__file__)
app_dir = os.path.abspath(os.path.join(current_script_path, "../../"))
project_dir = os.path.abspath(os.path.join(current_script_path, "../../../"))

class SymbolHandler():
    def __init__(self, db):
        self.db = db
        
    def find_symbol_list_by_country(self, country):
        sql = text(f'''
                    select symbol
                    from investment_analyst.symbols
                    where country = '{country}'
                ''')
        return self.db.execute(sql).fetchall()
    
    def find_symbol_infos_by_symbols(self, symbol_list):
        symbol_seg = ""
        for symbol in symbol_list:
            if symbol_seg != "":
                symbol_seg = symbol_seg + ","
            symbol_seg = symbol_seg + "'" + symbol + "'"
            
        sql = text(f'''
                    select symbol, name
                    from investment_analyst.symbols
                    where symbol in ({symbol_seg})
            ''')
        return self.db.execute(sql).fetchall()

    def update_symbol_list(self, symbol_info_list):
        sql = text('''
            insert into investment_analyst.symbols (
                symbol, name, country, market
            )
            values (
              :symbol, :name, :country, :market  
            )
            on duplicate key update
                name = VALUES(name),
                country = VALUES(country),
                market = VALUES(market)
        ''')
        self.db.execute(sql, symbol_info_list)
        
    def delete_symbol(self, delete_symbol_list):
        sql = text('''
            delete from investment_analyst.symbols
            where symbol in ('{0}')
        '''.format("','".join(delete_symbol_list))
        )
        self.db.execute(sql, symbol_info_list)