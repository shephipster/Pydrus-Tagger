import bisect
class ProcessedFilesIo:
    HASH_FILE = "tempFiles/hashFiles.txt"
    hashes = list()

    def __init__(self):     
        #ensure exists
        ProcessedFilesIo.load()  

    def hashInFile(self, hashcode):
        """ For now we'll just assume the system has the space to keep all ids in memory"""
        return hashcode in ProcessedFilesIo.hashes
        #TODO: Binary search

    def load():
        file = open(ProcessedFilesIo.HASH_FILE, 'r')
        for line in file:
            info = line.strip()
            if not info == "":
                bisect.insort(ProcessedFilesIo.hashes, info)
        file.close()
        
    def addHash(self, hashcode):
        if not ProcessedFilesIo.hashInFile(self, hashcode):
            bisect.insort(ProcessedFilesIo.hashes, hashcode)

    def save(self):
        with open(ProcessedFilesIo.HASH_FILE, 'w') as file:
            file.seek(0)
            for hash in ProcessedFilesIo.hashes:
                file.write(f'{hash}\n')