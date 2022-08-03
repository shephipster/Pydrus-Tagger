from .Entity import Entity
import sql.Connection

class Guilds(Entity):
    """
    guild_id : int
    owner_id: User
    name : str
    """
    
    def __init__(self):
        super().__init__("Guilds")
        
    def createTable(self):
        connection = sql.Connection.connection.cursor()
        table = \
        """
        CREATE TABLE IF NOT EXISTS
        Guilds(
            guild_id integer PRIMARY KEY,
            owner_id integer,
            name text NOT NULL      ,
            FOREIGN KEY (owner_id)
                REFERENCES Users (user_id) 
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
        connection = sql.Connection.connection.cursor()

        if self.getByPKey(kwargs['guild_id']):
            query = \
            """
            UPDATE Guilds SET
            name = ? 
            where guild_id = ?
            """
            params = (
                kwargs['name'],   
                kwargs['guild_id'],         
            )
        else:
            query = \
            """
            INSERT INTO Guilds VALUES (?, ?, ?)
            """
            params = (
                kwargs['guild_id'],
                kwargs['owner_id'],
                kwargs['name'],            
            )

        connection.execute(query, params)
    
    def getByPKey(self, pkey):
        connection = sql.Connection.connection.cursor()
        query = f'SELECT * from Guilds where guild_id = {pkey}'
        fetched_data = connection.execute(query).fetchall()
        return fetched_data
    
    def search(self, **kwargs):
        pass

    def set(self, pkey, **kwargs):
        pass