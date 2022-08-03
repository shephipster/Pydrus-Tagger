from abc import ABC, abstractmethod

class Entity(ABC):
    
    def __init__(self, name:str):
        self.name = name
        
    @abstractmethod
    def createTable(self):
        pass
    
    @abstractmethod
    def addRow(self, **kwargs):
        pass

    @abstractmethod
    def convertFromRow(self, values:list):
        pass
    
    @abstractmethod
    def getByPKey(self, pkey):
        pass

    @abstractmethod
    def search(self, **kwargs):
        pass

    @abstractmethod
    def set(self, pkey, **kwargs):
        pass