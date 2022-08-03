from .Entity import Entity
import sql.Connection

class User_Channel_Mappings(Entity):
    
    def __init__(self):
        super().__init__("User_Channel_Mappings")
        
    def createTable(self):
        connection = sql.Connection.connection.cursor()
        table = \
        """
        CREATE TABLE IF NOT EXISTS
        User_Channel_Mappings(
            id integer PRIMARY KEY,
            user_id integer NOT NULL,
            channel_id integer NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES Users (user_id)
                    ON DELETE CASCADE,
            FOREIGN KEY (channel_id)
                References Guilds (channel_id)
                    ON DELETE CASCADE                   
        );
        """
        try:
            connection.execute(table)
        except Exception as e:
            print(e)
    
        
    def convertFromRow(self, values: list):
        return super().convertFromRow(values)
    
    def addRow(self, **kwargs):
        return super().addRow(**kwargs)
    
    def getByPKey(self, pkey):
        return super().getByPKey(pkey)

    def search(self, **kwargs):
        pass

    def set(self, pkey, **kwargs):
        pass