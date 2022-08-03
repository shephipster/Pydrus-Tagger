from .Entity import Entity
import sql.Connection

class User_Guild_Mappings(Entity):
    
    def __init__(self):
        super().__init__("User_Guild_Mappings")
        
    def createTable(self):
        connection = sql.Connection.connection.cursor()
        table = \
        """
        CREATE TABLE IF NOT EXISTS
        User_Guild_Mappings(
            id integer PRIMARY KEY,
            user_id integer NOT NULL,
            guild_id integer NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES Users (user_id)
                    ON DELETE CASCADE,
            FOREIGN KEY (guild_id)
                References Guilds (guild_id)
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