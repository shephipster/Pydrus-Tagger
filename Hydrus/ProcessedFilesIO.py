import bisect
import os
class ProcessedFilesIO:
    hashes = list()
    file: str

    def __init__(self, file):     
        #ensure exists
        self.file = file
        ProcessedFilesIO.load(file)  

    def hashInFile(self, hashcode):
        """ For now we'll just assume the system has the space to keep all ids in memory"""
        return hashcode in ProcessedFilesIO.hashes

    def load(file):
        file = open(file, 'r')
        for line in file:
            info = line.strip()
            if not info == "":
                bisect.insort(ProcessedFilesIO.hashes, info)
        file.close()
        
    def addHash(self, hashcode):
        if not ProcessedFilesIO.hashInFile(self, hashcode):
            bisect.insort(ProcessedFilesIO.hashes, hashcode)

    def save(self):
        with open(self.file, 'w') as file:
            file.seek(0)
            for hash in ProcessedFilesIO.hashes:
                file.write(f'{hash}\n')