class ProcessedFilesIO:
    hashes: dict
    file: str
    id: int

    def __init__(self, file):     
        #ensure exists
        self.file = file
        self.id = 0
        self.hashes = dict()
        ProcessedFilesIO.load(self, file)  

    def hashInFile(self, hashcode):
        """ For now we'll just assume the system has the space to keep all ids in memory"""
        return hashcode in self.hashes.keys()

    def load(self, file):
        file = open(file, 'r')
        for line in file:
            info = line.strip()
            if not info == "":
                self.hashes[self.id] = info
                self.id = self.id + 1
        file.close()
        
    def addHash(self, hashcode):
        if not ProcessedFilesIO.hashInFile(self, hashcode):
            self.hashes[self.id] = hashcode
            self.id = self.id + 1

    def save(self):
        with open(self.file, 'w') as file:
            file.seek(0)
            for hash in self.hashes:
                file.write(f'{hash}\n')