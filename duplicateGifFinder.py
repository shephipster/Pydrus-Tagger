#To identify gifs that are similar but maybe are misaligned cuts, we need to move them around.
#For example, if they can be viewed as having come from the same scene but with one being frames 1-100 and the other frames 15-115 then we should count them
from PIL import Image
import imagehash
from scipy.spatial import distance
from Hydrus import HydrusApi, ProcessedFilesIO
import io

def gifToHashSet(img:Image, hashSize:int=8):
    imageHashSet = []
    for frame in range(0, img.n_frames):
        img.seek(frame)
        hash = imagehash.phash(image=img, hash_size=hashSize)
        imageHashSet.append(hash)
    return imageHashSet

def splitGifIntoHashSet(file:str, hashSize:int = 8):
    #split a gif image into its set of images and their hashes, returning the hash set
    image:Image = Image.open(file)
    imageHashSet = []
    for frame in range(0, image.n_frames):
        image.seek(frame)
        hash = imagehash.phash(image=image, hash_size=hashSize)
        imageHashSet.append(hash)
    return imageHashSet

def areSimilar(setOne:list, setTwo:list, hashSize:int = 8, distanceLimit:int = 2, percentSimilar:int = 80):
    lengthOne = len(setOne)
    lengthTwo = len(setTwo)
    lengthSubsetOne = int(len(setOne) * percentSimilar / 100)
    lengthSubsetTwo = int(len(setTwo) * percentSimilar / 100)

    if lengthSubsetOne > lengthSubsetTwo:
        searchLength = lengthSubsetTwo
    else:
        searchLength = lengthSubsetOne

    for i in range(0, lengthOne-searchLength):
        subsetOne = setOne[i:i+searchLength]
        for j in range(0, lengthTwo-searchLength):
            subsetTwo = setTwo[j:j+searchLength]
            match = True
            for k in range(0, searchLength):
                lim = hashSize
                if len(subsetOne[k].hash) < lim:
                    lim = len(subsetOne[k].hash)
                if len(subsetTwo[k].hash) < lim:
                    lim = len(subsetTwo[k].hash)
                for l in range(0, lim):
                    itemOne = subsetOne[k].hash[l]
                    itemTwo = subsetTwo[k].hash[l]
                    dist = distance.hamming(itemOne, itemTwo) * hashSize
                    if dist > distanceLimit:
                        return False
                if match == False:
                    break
            if match:
                #there was no point in the check where the hamming distance was too great, consider it a match
                return True
    #went through every single alignment without returning early, means there was no match
    return False

def areTwoGifsSimilar(pathToFileOne:str, pathToFileTwo:str, percentFramesSimilar:int = 80, hammingDistanceLimit:int = 8, hashSize:int = 8):
    hashSetOne = splitGifIntoHashSet(pathToFileOne, hashSize=hashSize)
    hashSetTwo = splitGifIntoHashSet(pathToFileTwo, hashSize=hashSize)
    return areSimilar(hashSetOne, hashSetTwo, distanceLimit=hammingDistanceLimit, percentSimilar=percentFramesSimilar, hashSize=hashSize)

def twoGifsAreSimilar(imgOne:Image, imgTwo:Image, percentFramesSimilar:int = 80, hammingDistanceLimit:int = 8, hashSize:int = 8):
    hashSetOne = gifToHashSet(imgOne)
    hashSetTwo = gifToHashSet(imgTwo)
    return areSimilar(hashSetOne, hashSetTwo, distanceLimit=hammingDistanceLimit, percentSimilar=percentFramesSimilar, hashSize=hashSize)

def findAllDuplicates(limit=1, hamDist=8, similarPercentFrames=80, hashSize:int = 8):
    fio = ProcessedFilesIO.ProcessedFilesIO("./tempFiles/processedGifHashes.txt")
    gifHashes = HydrusApi.getAllFilesOfType('gif')
    workingHashes = []

    #get ones that need processing
    for entry in gifHashes:
        if not fio.hashInFile(entry):
            workingHashes.append(entry)

    upperLimit = len(workingHashes)
    if limit > 0:
        upperLimit = limit
    
    for i in range(0,upperLimit):
        workingBytes = HydrusApi.getImageBytesByHash(workingHashes[i])
        workingImage = Image.open(workingBytes)
        for hash in gifHashes:  #This can be optimized by just pulling in large numbers of gifs at once from Hydrus, cutting down on API calls. For now this'll work just slowly
            if hash == workingHashes[i]:
                continue
            checkBytes = HydrusApi.getImageBytesByHash(hash)
            checkImage = Image.open(checkBytes)
            if twoGifsAreSimilar(workingImage, checkImage,hammingDistanceLimit=hamDist, percentFramesSimilar=similarPercentFrames, hashSize=hashSize):
                HydrusApi.addHashesToPage("Duplicate Gifs", workingHashes[i], hash)
        fio.addHash(workingHashes[i])
        print("Finished processing file with hash ", workingHashes[i])
        fio.save()


#It does work to a certain extent, but holy hell it is slow AND it has a good number of false positives.
#The main issue is that short gifs only need to get lucky against big gifs. A gif with 1 frame only needs
#have its one frame be kinda similar to a single frame of a gif with, say, 100 frames
#Not really anything that can be done about it that I can think of, if you can go at it
findAllDuplicates(3, hamDist=2,similarPercentFrames=80, hashSize = 64)