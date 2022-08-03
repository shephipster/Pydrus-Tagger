from .Entity import Entity
from datetime import datetime, timedelta
import sql.Connection

class Users(Entity):
    
    def __init__(self):
        super().__init__("Users")
        
    def createTable(self):
        connection = sql.Connection.connection.cursor()
        table = \
        """ CREATE TABLE IF NOT EXISTS Users(
            user_id integer PRIMARY KEY,
            name text NOT NULL,
            last_ping DATETIME NOT NULL,
            notify boolean NOT NULL,
            ping_delay integer NOT NULL,
            specify_tags boolean NOT NULL);
        """
        try:
            connection.execute(table)
            sql.Connection.connection.commit()
            connection.close()
        except Exception as e:
            print(e)
        
    def convertFromRow(self, values: list):
        return super().convertFromRow(values)
    
    def setValue(self, pkey, col, value):
        query = \
        """
        UPDATE Users SET
        twitter = ?
        where user_id = ?
        """
        params = (pkey, )
    
    def addRow(self, **kwargs):
        
        connection = sql.Connection.connection.cursor()

        #check if user already exists
        if self.getByPKey(kwargs['user_id']):
            query = \
            """
            UPDATE Users SET 
            name = ? ,
            last_ping = ?
            where user_id = ?
            """
            params = (kwargs['name'], datetime.now(), kwargs['user_id'])
        else:
            query = \
            """
            INSERT INTO Users VALUES (?,?,?,?,?,?);
            """
            params = (
                kwargs['user_id'],
                kwargs['name'],
                (datetime.now() - timedelta(hours=1)),
                True,
                30,
                True,
            )
            
        connection.execute(query, params)
        sql.Connection.connection.commit()
        connection.close()
        
    def updateTime(self, user_id):
        query = \
        """
        UPDATE Users SET 
        last_ping = ?
        where user_id = ?
        """
        params = (datetime.now(), user_id)
        connection = sql.Connection.connection.cursor()
        connection.execute(query, params)
        
    def getByPKey(self, pkey):
        connection = sql.Connection.connection.cursor()
        query = f'SELECT * from Users where user_id = {pkey}'
        fetched_data = connection.execute(query).fetchall()
        sql.Connection.connection.commit()
        connection.close()
        return fetched_data
    
    def search(self, **kwargs):
        pass

    def set(self, pkey, **kwargs):
        pass

        
        