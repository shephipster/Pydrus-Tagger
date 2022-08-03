from .Entity import Entity
import sql.Connection

class User_Tag_Mappings(Entity):
    
    def __init__(self):
        super().__init__("User_Tag_Mappings")
        
    def createTable(self):
        connection = sql.Connection.connection.cursor()
        table = \
        """
        CREATE TABLE IF NOT EXISTS
        User_Tag_Mappings(
            id integer PRIMARY KEY AUTOINCREMENT,
            user_id integer NOT NULL,
            guild_id integer NOT NULL,
            tag text NOT NULL,
            blacklist boolean NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES Users (user_id)  
                    ON DELETE CASCADE,
            FOREIGN KEY (guild_id)
                REFERENCES Guilds (guild_id)
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

        if self.getByPKey(None, tag = kwargs['tag'], user_id = kwargs['user_id'], guild_id = kwargs['guild_id'], blacklist = kwargs['blacklist']):
            return
        else:
            query = \
            """
            INSERT INTO User_Tag_Mappings (user_id, guild_id, tag, blacklist) VALUES (?,?,?,?)
            """
            params = (
                kwargs['user_id'],
                kwargs['guild_id'],
                kwargs['tag'],
                kwargs['blacklist']          
            )

        connection.execute(query, params)
        
    def deleteRow(self, **kwargs):
        try:
            connection = sql.Connection.connection.cursor()
            guid = kwargs['guild_id']
            uid = kwargs['user_id']
            tag = kwargs['tag']
            query = f'DELETE from User_Tag_Mappings where guild_id = ? AND user_id = ? AND tag = ? AND blacklist = ?'
            params = (guid, uid, tag, kwargs['blacklist'])
            fetched_data = connection.execute(query, params).fetchall()
            return fetched_data
        except:
            return None
        
    def search(self, **kwargs):
        try:
            connection = sql.Connection.connection.cursor()
            params = ()
            query = f'SELECT * from User_Tag_Mappings where '
            if 'user_id' in kwargs:
                query = query + "user_id = ?"
                params = params + (kwargs['user_id'],)
            if 'guild_id' in kwargs:
                if len(params) != 0:
                    query = query + " AND "
                query = query + "guild_id = ?"
                params = params + (kwargs['guild_id'],)
            if 'tag' in kwargs:
                if len(params) != 0:
                    query = query + " AND "
                query = query + "tag= ?"
                params = params + (kwargs['tag'],)
            if 'blacklist' in kwargs:
                if len(params) != 0:
                    query = query + " AND "
                query = query + "blacklist = ?"
                params = params + (kwargs['blacklist'],)
                
            fetched_data = connection.execute(query, params).fetchall()
            return fetched_data
        except:
            return                 
    
    def getByPKey(self, pkey, **kwargs):
        try:
            connection = sql.Connection.connection.cursor()
            guid = kwargs['guild_id']
            uid = kwargs['user_id']
            tag = kwargs['tag']
            query = f'SELECT * from User_Tag_Mappings where guild_id = ? AND user_id = ? AND tag = ? AND blacklist = ?'
            params = (guid, uid, tag, kwargs['blacklist'])
            fetched_data = connection.execute(query, params).fetchall()
            return fetched_data
        except:
            return None
        
    def search(self, **kwargs):
        pass

    def set(self, pkey, **kwargs):
        pass