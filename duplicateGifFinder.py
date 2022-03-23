#To identify gifs that are similar but maybe are misaligned cuts, we need to move them around.
#For example, if they can be viewed as having come from the same scene but with one being frames 1-100 and the other frames 15-115 then we should count them
from PIL import Image
import imagehash
from scipy.spatial import distance

def splitGifIntoHashSet(file:str, hashSize:int = 8):
    #split a gif image into its set of images and their hashes, returning the hash set
    image:Image = Image.open(file)
    imageHashSet = []
    for frame in range(0, image.n_frames):
        image.seek(frame)
        hash = imagehash.phash(image=image, hash_size=hashSize)
        imageHashSet.append(hash)
    return imageHashSet

def areSimilar(setOne:list, setTwo:list, hashSize:int = 8, distanceLimit:int = 10, percentSimilar:int = 80):
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
                for l in range(0, hashSize):
                    itemOne = subsetOne[k].hash[l]
                    itemTwo = subsetTwo[k].hash[l]
                    dist = distance.hamming(itemOne, itemTwo) * hashSize
                    if dist > distanceLimit:
                        match = False
                        break
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