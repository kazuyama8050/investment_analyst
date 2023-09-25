from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

class DbHandler:
    __instance = None
    __db_session = None
    
    def __init__(self):
        DbHandler.__instance = self
        
    @staticmethod
    def get_instance():
        if DbHandler.__instance == None: DbHandler()
        return DbHandler.__instance
    
    def get_session(self):
        if self.__db_session is None:
            raise RuntimeError("You need to do 'set_session' before using 'get_session()'")
        return self.__db_session
    
    def set_session(self, db_config, db_name):
        engine = create_engine('mysql+mysqlconnector://{user}:{password}@{host}/{db_name}'.format(
            host = db_config.get("db", "host"),
            user = db_config.get("db", "user"),
            password = db_config.get("db", "password"),
            db_name = db_name
        ))
        
        Session = sessionmaker(bind=engine)
        self.__db_session = Session()
    
    def close_session(self):
        if self.__db_session is not None: self.__db_session.close()