from .Entity import Entity
import sql.Connection

class Channels(Entity):
    
    def __init__(self):
        super().__init__("Channels")
        
    def createTable(self):
        connection = sql.Connection.connection.cursor()
        table = \
        """
        CREATE TABLE IF NOT EXISTS
        Channels(
            channel_id integer PRIMARY KEY,
            name text NOT NULL,
            nsfw boolean NOT NULL,
            guild_id integer NOT NULL,
            FOREIGN KEY (guild_id)
                REFERENCES Guilds (guild_id)           
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
        
        if self.getByPKey(kwargs['channel_id']):
            query = \
            """
            UPDATE Channels SET
            name = ?,
            nsfw = ?
            where channel_id = ?
            """
            params = (
                kwargs['name'],
                kwargs['nsfw'],
                kwargs['channel_id']
            )
            
        else:
            query = \
            """
            INSERT INTO Channels VALUES (?,?,?,?);
            """
            params = (
                kwargs['channel_id'],
                kwargs['name'],
                kwargs['nsfw'],
                kwargs['guild_id']
            )
        
        connection.execute(query, params)
    
    def getByPKey(self, pkey):
        connection = sql.Connection.connection.cursor()
        query = f'SELECT * from Channels where channel_id = {pkey}'
        fetched_data = connection.execute(query).fetchall()
        return fetched_data
        
    def search(self, **kwargs):
        pass

    def set(self, pkey, **kwargs):
        pass