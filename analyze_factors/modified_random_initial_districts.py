#generateRandomInitialDistricts.py
#Quantifying Gerrymandering, Duke University
#dataPlus2018
#Author: Sam Eure
#Generates random initial districts of chosen maps
#Need the centroid and neighbor lists of the precincts in the map chosen

#IMPORTANT NOTE: Code is written for the python 2.7 version. You will need to change print statments, etc., for 
#           The code to be compatable for python3.0 or later

#**************************************************************
#++++++++++++++++++++++++ INPUT +++++++++++++++++++++++++++++++
#--------------------------------------------------------------
#Number of different random districtings
numMaps       = 2

#Number of actual districts per map
numDists      = 8

#Population difference max

maxDifference = 0.05


#Path Finders
#dataDirPath   = "../../CuratedData/"
#outFilePrefix = "../../RandomDistricts/"
#dataDirPath = "../../CuratedData/"
dataDirPath = "~/mathingly/"

mapType    = "MID_CROSS"
mapChosen     = "MDPrecinct_"+mapType
#outFilePrefix = "../../../MDSamplingData/SamplingData/"+mapType+"/" +"Random"
outFilePrefix = "~/mathingly/"

dataPrefix    = "Precinct"
POPULATION    = "POPULATION"
NEIGHBORS     = "Adjusted_Neighbors"
CENTROIDS     = "LATLONG"
AREA          = "AREAS"
dataType      = "Raw"




#FOR UNION_ANSON
#dataDirPath   = "../../CuratedData/"
#outFilePrefix = "../../RandomDistricts/"
#mapChosen    = "UnionPrecinctAnsonCounty"
#dataPrefix       = "UnionPrecinctAnsonCounty"
#NEIGHBORS        = "_NEIGHBORS"
#CENTROIDS        = "_CENTROIDS"
#AREA         = "_AREAS"
#POPULATION    = "_POPULATION"


#*******************************************************************************
#+++++++++++++++++++++ BEGIN SCRIPT ++++++++++++++++++++++++++++++++++++++++++++
#------------------------------------------------------------------------------- 
import os
import time
import shutil
import random
#*******************************************************************************
#+++++++++++++++++++++ Helper Functions ++++++++++++++++++++++++++++++++++++++++
#------------------------------------------------------------------------------- 
class node:
    identity = -1
    population = 0;
    precincts = set()
    centroid = [0.0,0.0]
    area = 0.0
    neighbors = set()

def initialize():
    newNode = node()
    newNode.identity = -1
    newNode.population = 0;
    newNode.precincts = set([])
    newNode.centroid = [0.0,0.0]
    newNode.area = 0.0
    newNode.neighbors = set([])
    return newNode

def showNode(N):
    print()
    print("identity: ",N.identity)
    print("population: ",N.population)
    print("precincts: ",N.precincts)
    print("centroid: ",N.centroid)
    print("area: ",N.area)
    print("neighbors: ",N.neighbors)
    return ""

def copyNode(A):
    a = initialize()
    a.identity = A.identity
    a.population = A.population
    a.precincts = A.precincts
    a.centroid = A.centroid
    a.area = A.area
    a.neighbors = A.neighbors
    return a

def distance(c1, c2):
    x1,y1 = c1
    x2,y2 = c2
    dX = x1-x2
    dY = y1-y2
    return (dX**2 + dY**2)**(1/2.0)



def compressGroups(Groups):

    groupA = Groups[random.randint(1,len(Groups))-1] #need the -1 to correct the range

    Groups.remove(groupA)

    groupB = findClosest(groupA, Groups)  

    Groups.remove(groupB)

    combGroup = combineNodes(groupA, groupB)

    Groups.append(combGroup)

    return Groups

def findClosest(groupA, Groups):

    closestGroup = initialize()

    minDist = 10**12

    potentialGroups = []

    for potentialGroup in Groups:

        if overlapping(potentialGroup.precincts, groupA.neighbors):
            potentialGroups.append(potentialGroup)

    if len(potentialGroups) == 0:
        print("ERROR: Group has no neighbors")
        showNode(groupA)
        exit()

    for g in potentialGroups:
        dist = distance(g.centroid, groupA.centroid)

        if dist > 0.0 and dist < minDist:
            if True:
                minDist = dist
                closestGroup = g

    return closestGroup

def compressCentroid(A,B):
    #Takes in two nodes and compresses their centroids into a single centroid
    #Proportions centroids based on the area of their respective nodes
    totArea = A.area + B.area
    weightA = A.area/(totArea+0.0)
    weightB = 1 - weightA
    centA = [t*weightA for t in A.centroid]
    centB = [t*weightB for t in B.centroid]
    newCent = [centA[i]+centB[i] for i in range(len(centA))]
    return newCent

def combineNodes(nodeA, nodeB):
    #Combines two nodes' populations, areas, centroids, and precinct composition
    newNode = initialize()

    newNode.centroid = compressCentroid(nodeA, nodeB)

    newNode.area += nodeA.area
    newNode.area += nodeB.area

    newNode.population += nodeA.population
    newNode.population += nodeB.population

    newNode.precincts.update(nodeA.precincts)
    newNode.precincts.update(nodeB.precincts)

    newNode.identity = min(nodeA.identity, nodeB.identity)

    newNode.neighbors.update(nodeA.neighbors)
    newNode.neighbors.update(nodeB.neighbors)

    newNode.neighbors = newNode.neighbors - newNode.precincts

    return newNode

def groomPopulations(Groups, groupMemory):
    #print("grooming")
    #If everything is going according to plan (i.e. a changeOccured)
    groupBig, groupSmall = findPair(Groups)
    #print("identityBig = ", groupBig.identity)
    #print("identitySmall = ", groupSmall.identity)

    Groups.remove(groupBig)
    Groups.remove(groupSmall)

    groupP = findPrecinct(groupBig, groupSmall, groupMemory)  

    #Check if a precinct which isn't a biconnected component was found:
    if groupP.identity == -1:
        #If the pair will not work:
        for run in range(28):
            Groups.append(groupBig)
            Groups.append(groupSmall)

            groupBig, groupSmall = tryAgain(groupBig, groupSmall, Groups)

            if (groupBig.identity == -1 or groupSmall.identity == -1):
                break

            Groups.remove(groupBig)
            Groups.remove(groupSmall)

            groupP = findPrecinct(groupBig, groupSmall, groupMemory) 

            if groupP.identity >= 0:
                break

    if groupP.identity == -1:
        print("Checkmate: No possible moves")
        return Groups, False

    groupBig   = takeAwayPrecinct(groupBig  , groupP, groupMemory)
    groupSmall =     combineNodes(groupSmall, groupP)

    Groups.append(groupBig)
    Groups.append(groupSmall)

    return Groups, True

def findPair(Groups):
    pair = []
    maxPopDiff = 0
    for g1 in Groups:
        #Now get all groups that contain a precinct which neighbors g1
        for g2 in Groups:
            if overlapping(g1.precincts, g2.neighbors) and (g1.population > g2.population):

                diff = g1.population - g2.population
                if diff > maxPopDiff:
                    maxPopDiff = diff
                    pair = [g1,g2]
            elif overlapping(g2.precincts, g1.neighbors) and (g2.population > g1.population):

                diff = g2.population - g1.population
                if diff > maxPopDiff:
                    maxPopDiff = diff
                    pair = [g2,g1]

    return pair 

def findPrecinct(groupBig, groupSmall, groupMemory):
    #finds the precinct in groupBig which is closest to groupSmall
    if not overlapping(groupBig.precincts, groupSmall.neighbors):
        print('\t', '\t', '\t', "Error240: Incorrect group pair | Check: findPair(Groups)")
        exit()

    groupReturned = initialize()

    preliminaryPrecincts = groupBig.precincts.intersection(groupSmall.neighbors)

    if len(preliminaryPrecincts) == 0:
        print('\t', '\t', '\t', "no preliminaryPrecincts, can't try again, need to abort")
        exit()

    #groupBigNodes = [g for g in groupMemory if g.identity in groupBig.precincts]

    startingPrecinct = list(groupBig.precincts)[0]
    bccList          = []
    visited          = [False] * len(groupMemory)
    depth            = [-2] * len(groupMemory)
    low              = [-2] * len(groupMemory)
    parent           = [-2] * len(groupMemory)

    findBiConnectedComponents(startingPrecinct, 0, groupBig.precincts, groupMemory, bccList, visited, depth, low, parent)


    candidatePrecincts = preliminaryPrecincts - set(bccList)

    if len(candidatePrecincts) == 0:
        return initialize()
        

    maxD = -10**10
    for p in candidatePrecincts:
        groupP = findGroupP(groupMemory, p)
        D = getDistance(groupP, groupBig, groupSmall)
        if D > maxD:
            maxD = D
            groupReturned = copyNode(groupP)

    return groupReturned

def getDistance(groupP, groupBig, groupSmall):

    d1 = distance(groupP.centroid, groupBig.centroid)
    d2 = distance(groupP.centroid, groupSmall.centroid)
    return d1-d2

def findGroupP(groupMemory, p):
    groupP = [g for g in groupMemory if g.identity == p]
    if len(groupP) != 1:
        print('\t', '\t', '\t', "Error: 291 | no node in groupMemory for precinct ", str(p))
        exit()
    groupP = groupP[0]
    return copyNode(groupP) #perfect

def tryAgain(groupBig, groupSmall, Groups):
    limitPopDiff = groupBig.population - groupSmall.population
    pair = [initialize(), initialize()]
    maxPopDiff = 0
    for g1 in Groups:
        #Now get all groups that contain a precinct which neighbors g1
        for g2 in Groups:
            if overlapping(g1.precincts, g2.neighbors) and (g1.population > g2.population):
                diff = g1.population - g2.population
                if diff > maxPopDiff and diff < limitPopDiff:
                    maxPopDiff = diff
                    pair = [g1,g2]
            elif overlapping(g2.precincts, g1.neighbors) and (g2.population > g1.population):
                diff = g2.population - g1.population
                if diff > maxPopDiff and diff < limitPopDiff :
                    maxPopDiff = diff
                    pair = [g2,g1]
    return pair


def takeAwayPrecinct(groupBig, groupP, groupMemory):

    #remove the precinct from the group's precincts
    groupBig.precincts.remove(groupP.identity)

    groupBig.neighbors = set([])

    #Recreating neighbors
    for p in groupBig.precincts:

        citizenGroup = findGroupP(groupMemory, p)
        groupBig.neighbors.update(citizenGroup.neighbors)

    groupBig.neighbors = groupBig.neighbors - groupBig.precincts

    #In case the precicnt removed was the idenity, re-label the identity
    #print(len(groupBig.precincts))
    groupBig.identity = min(groupBig.precincts)

    #Adjust the area
    wholeArea = groupBig.area

    groupBig.area -= groupP.area

    groupBig.population -= groupP.population

    #Reverse adjust the location of the centroid
    fracPopP = groupP.area/wholeArea
    groupBig.centroid[0] = groupBig.centroid[0] - fracPopP*groupP.centroid[0]
    groupBig.centroid[1] = groupBig.centroid[1] - fracPopP*groupP.centroid[1]

    return groupBig

def populationsDifferent(Groups, idealPop):
    minPop = idealPop * (1-maxDifference)
    maxPop = idealPop * (1+maxDifference)
    for g in Groups:
        if g.population > maxPop or g.population < minPop:
            return True
    return False

def overlapping(A,B):
    C  = A.union(B)
    return not (len(C) == (len(A) + len(B)))

def showMaxPopDiff(Groups,idealPop):
    maxPop = 0
    minPop = 10000000
    groupPops = []
    for g in Groups:
        thisPop = g.population
        groupPops.append(thisPop)
        if thisPop > maxPop:
            maxPop = thisPop
        if thisPop < minPop:
            minPop = thisPop
    a = maxPop - idealPop
    b = idealPop - minPop
    return (max(a,b)/idealPop)*100, groupPops

def findBiConnectedComponents(i, d, precincts, groupMemory, bccList, visited, depth, low, parent):
    visited[i] = True
    depth[i] = d
    low[i] = d
    childCount = 0
    isArticulation = False
    adj = groupMemory[i].neighbors.intersection(set(precincts)) #neighborlist
    for ni in adj:
        if not visited[ni]:
            parent[ni] = i
            findBiConnectedComponents(ni, d + 1, precincts, groupMemory, bccList, visited, depth, low, parent)
            childCount = childCount + 1
            if low[ni] >= depth[i]:
                isArticulation = True
            low[i] = min(low[i], low[ni])
        elif ni != parent[i]:
            low[i] = min(low[i], depth[ni])
    if (parent[i] != -2 and isArticulation) or (parent[i] == -2 and childCount > 1):
        bccList.append(i)

#*******************************************************************************
#+++++++++++++++++++++ SCRIPT BODY +++++++++++++++++++++++++++++++++++++++++++++
#------------------------------------------------------------------------------- 

def readCentroids():
    #------- Prepare precincts/districts -------------------------------------------
    #opening
    centroidFileOpened   = open(os.path.join(dataDirPath, mapChosen, dataPrefix + CENTROIDS  +".txt"))
    populationFileOpened = open(os.path.join(dataDirPath, mapChosen, dataPrefix + POPULATION + ".txt"))
    areaFileOpened       = open(os.path.join(dataDirPath, mapChosen, dataPrefix + AREA       + ".txt"))
    neighborFileOpened   = open(os.path.join(dataDirPath, mapChosen, dataPrefix + NEIGHBORS  + ".txt"))

    #reading
    centroidFile = [a.split("\t") for a in centroidFileOpened.readlines()]
    neighborFile = [a.split("\t") for a in neighborFileOpened.readlines()]
    populationFile = [a.split("\t") for a in populationFileOpened.readlines()]
    areaFile = [a.split("\t") for a in areaFileOpened.readlines()]


    #closing
    centroidFileOpened.close()
    neighborFileOpened.close()
    populationFileOpened.close()
    areaFileOpened.close()

    #Preparing initial nodes
    totalPop = 0
    groupMemory = []

    for index in range(len(centroidFile)):
        nextNode = initialize()
        #prepare centroid
        Cent = centroidFile[index]
        Cent[2]=Cent[2].replace("\n","")
        Cent = [float(c) for c in Cent]
        nextNode.centroid = Cent[1:]
        #Distinguish the node and the centroids that the node contains
        nextNode.identity = int(Cent[0])
        nextNode.precincts.add(nextNode.identity)
        #find population and area
        nextNode.population += int(populationFile[index][1])
        totalPop            += nextNode.population
        nextNode.area       += float(areaFile[index][1])

        #prepare neighbors
        print(index)
        myNeighbors = neighborFile[index]

        if "\n" in myNeighbors:
            myNeighbors.remove("\n")
        if "" in myNeighbors:
            myNeighbors.remove("")

        myNeighbors = set([int(n) for n in myNeighbors])

        if -1 in myNeighbors:
            myNeighbors.remove(-1)

        if nextNode.identity in myNeighbors:
            myNeighbors.remove(nextNode.identity)

        nextNode.neighbors.update(myNeighbors)
        groupMemory.append(nextNode)

    idealPop = totalPop/(0.0+numDists)

#************************************************************************************************
#----- Starting Algorithm -----------------------------------------------------------------------

def generateRandomInitialDistricting(groupMemory, numDists, numMaps, idealPop):
    print("Starting with ", len(groupMemory), " precints")
    groupList = []

    i = 0
    while i < numMaps:
        print()
        print("Working on map ", str(i))
        
        #Reset Groups to initial conditions
        Groups = [copyNode(g) for g in groupMemory]

        #********************************************************************************************
        #----- COMPRESSION --------------------------------------------------------------------------
        
        while(len(Groups) > numDists):
            Groups = compressGroups(Groups)

        #********************************************************************************************
        #----- POPULATION ---------------------------------------------------------------------------
        #Ensure the algorithm is going according to plan
        maxPopPrevious = -1.0
        lastSwap = [[],[],[]]  #keep track of swaps occuring
        changeOccured = True  

        while(populationsDifferent(Groups, idealPop) and changeOccured):
            Groups, changeOccured = groomPopulations(Groups, groupMemory)
            currentMaxPopDev, allPops = showMaxPopDiff(Groups,idealPop)

            lastSwap[2] = lastSwap[1]
            lastSwap[1] = lastSwap[0]
            lastSwap[0] = allPops

            if currentMaxPopDev != maxPopPrevious:
                maxPopPrevious = currentMaxPopDev

            if lastSwap[0] == lastSwap[2]:
                print("Stuck in infinite swaps")
                changeOccured = False
        if not changeOccured:
            print()
            print("Dodging problematic map")
            print()
            continue

        groupList.append(Groups)
        i+=1

    print()
    print("Done.")

    return groupList
