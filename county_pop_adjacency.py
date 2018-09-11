
#v2 introduced custom classes for more readable (possibly slower) code

filename = 'county_pop_adjacency.txt' #file containing populations and adjacencies of all counties
ndistricts = 50 #50 for senate, 120 for house
err = 0.05 #5%
samplesize = 100000 #100000 takes a few (3 ish) hours to run on my computer

#parse input file
f = open(filename, 'r')
lines = []
for line in f:
    lines.append(line.strip().split(','))
f.close()

POPS = {} #county (str) -> population (int)
ADJS = {} #county (str) -> list of county (list of str)
COUNTIES = set() #set of county (set of str)
for line in lines:
    POPS[line[0]] = int(line[1])
    adj = line[2:]
    adj.remove(line[0]) #counties are duplicated in input file
    ADJS[line[0]] = set(adj)
    COUNTIES.add(line[0])

totalpop = sum(POPS.values())
ideal = totalpop / ndistricts
MINDIST = ideal * (1-err)
MAXDIST = ideal * (1+err)

temp = sorted(COUNTIES) #in this case, alphabetical order. Could try population, geographic, or random in the future
ORDER = {}
for i in range(len(temp)):
    ORDER[temp[i]] = i
ORDERF = lambda x: min(x, key=lambda y:ORDER[y])
del temp

class Cluster: #essentially a hashable set of counties with nice functions defined
    def __init__(self, countyset, population, small=None):
        self.val = countyset
        self.pop = population
        if small is None:
            self.small = min(countyset, key=min) #smallest element, used for faster hashing
        else:
            self.small = small
        self.work = int(self.pop / MINDIST) > int(self.pop / MAXDIST) #is the cluster satisfied?
    def __hash__(self):
        return hash(self.small)
    def __eq__(self, other):
        return self.val == other.val
    def __ne__(self, other):
        return not (self.val == other.val)
    def __add__(self, other): #union sets, add populations, min small. work is recalculated in __init__
        return Cluster(set.union(self.val, other.val),
                       self.pop + other.pop, min(self.small, other.small))
    def __len__(self):
        return len(self.val)
    def __iter__(self):
        return iter(self.val)
    def __repr__(self):
        return str(self.val)
    def __str__(self):
        return str(self.val)

class Clusters: #essentially a set of Cluster with adjacencies and nice functions
    def __init__(self, clusterset, adjs, work=None):
        self.val = clusterset
        self.adjs = adjs #adjacency matrix (Cluster -> set of Cluster)
        if work is None:
            self.work = sum(len(cluster) for cluster in clusterset if cluster.work) #how many counties are satisfied?
        else:
            self.work = work
    def __hash__(self):
        return hash(tuple(tuple(sorted(cluster.val)) for cluster in sorted(self.val, key=min)))
    def __eq__(self, other):
        return self.val == other.val
    def __ne__(self, other):
        return not (self.val == other.val)
    def __len__(self):
        return len(self.val)
    def __iter__(self):
        return iter(self.val)
    def tocombine(self, cluster1, cluster2):
        '''The "fast" bit of Clusters.combine: clusterset and work'''
        newcluster = cluster1 + cluster2
        newclusterset = [newcluster]
        for cluster in self.val:
            if cluster != cluster1 and cluster != cluster2:
                newclusterset.append(cluster)
        
        newwork = self.work
        if newcluster.work:
            newwork += len(newcluster)
        
        return (tuple(sorted(newclusterset, key=min)), newwork)
    def combine(self, cluster1, cluster2):
        '''Combine cluster1 and cluster2 (edge contraction)'''
        newcluster = cluster1 + cluster2
        newclusterset = [newcluster]
        
        newadjs = {newcluster: set.union(self.adjs[cluster1], self.adjs[cluster2])}
        newadjs[newcluster].remove(cluster1)
        newadjs[newcluster].remove(cluster2)
        
        for cluster in self.val:
            if cluster != cluster1 and cluster != cluster2:
                newclusterset.append(cluster)
                newadjs[cluster] = self.adjs[cluster] #contract rows
        
        for cluster in newadjs[newcluster]: #contract columns. Most expensive single step; can't be improved afaik without changing data structure
            newset = set()
            for adjcluster in self.adjs[cluster]:
                if adjcluster == cluster1 or adjcluster == cluster2:
                    newset.add(newcluster)
                else:
                    newset.add(adjcluster)
            newadjs[cluster] = newset
        
        newwork = self.work
        if newcluster.work:
            newwork += len(newcluster)
        
        return Clusters(newclusterset, newadjs, newwork)

def pretty(S):
    '''Human-readable string format of Clusters object'''
    out = str(len(S)) + '\n'
    for cluster in sorted(S, key=lambda x: x.pop, reverse=True):
        out = out + str(int(cluster.pop / MINDIST)) + ': '
        if not cluster.work:
            out = out + '*'
        for county in cluster:
            out = out + county + ', '
        out = out[:-2] + '\n'
    return out

def binarysearch(a, L):
    start = 0
    end = len(L)
    while end > start:
        if a == L[(start+end)//2]:
            return (start+end)//2
        if a < L[(start+end)//2]:
            start = (start+end)//2 + 1
        else:
            end = (start+end)//2
    return start

def main(samplesize):
    out = [] #output
    
    #base case: all clusters are one county
    newadjs = {}
    for county in COUNTIES:
        newadjs[Cluster({county}, POPS[county])] = \
                                  {Cluster({county2}, POPS[county2]) for county2 in ADJS[county]}
    L = [Clusters([Cluster({county}, POPS[county]) for county in COUNTIES], newadjs)] #list of Clusters
    
    i = 0 #number of edge contracts
    j = 1 #total number of results prior to pruning
    while len(L) > 0:
        print(len(L[0]), max(S.work for S in L), min(S.work for S in L), len(L), j, end=' ')
        j = 0
        
        newclusters = set() #set of Clusters.val to prune duplicates
                           #set of tuple(sorted(Clusters.val)) = set of tuple of str
        satisfied = [] #list of number of satisfied counties for each new Clusters to prune poor moves
                       #list of int, kept sorted
        pairs = [] #vertices in edge contractions, helps reduce memory usage by saving Clusters.combine for last
                   #list of list (keep track of S) of tuple of Cluster, kept sorted (same order as satisfied)
        
        printed = False #intermediate step printing flag
        for S in L: #S: Clusters type
            pairs.append([])
            
            #sort primarily on number of possible moves, then secondarily on ORDER
            #(order of operations is backwards)
            #we will stop if there are no options for a Cluster, and take forced moves (one option)
            #this kills bad branches early and reduces branching factor
            ordering = sorted(S, key=ORDERF)
            ordering.sort(key=lambda x: len([y for y in S.adjs[x] if not y.work]))
            
            for cluster1 in ordering:
                if not cluster1.work:
                    for cluster2 in S.adjs[cluster1]:
                        if not cluster2.work: #potential edge dissolution
                            j += 1
                            r = S.tocombine(cluster1, cluster2)
                            #if (good enough move) and (not done before): add to next generation
                            if (len(satisfied) < samplesize or r[1] >= satisfied[-1]) and (r not in newclusters):
                                index = binarysearch(r[1], satisfied) #where to insert?
                                newclusters.add(r)
                                satisfied.insert(index, r[1])
                                pairs[-1].insert(index, (cluster1, cluster2))
                                if len(satisfied) > samplesize: #delete the worst move
                                    satisfied.pop()
                                    pairs[-1].pop()
                                    newclusters.remove(sorted(newclusters, key=lambda x: x[1])[0]) #not strictly necessary, but memory
                                    if not printed:
                                        print('.', end='')
                                        printed = True
                    break #we break here to reduce branching factor (moves are all local). Could try not breaking here
            else: #all clusters .work -> completed clustering
                out.append(S)
        del satisfied, newclusters #memory
        if not printed:
            print('.', end='')
        print('.', end='')
        
        #now we must Clusters.combine all pairs
        newL = []
        for Si in range(len(pairs)):
            for pair in pairs[Si]:
                newL.append(L[0].combine(pair[0], pair[1]))
            L.pop(0) #memory
        L = newL
        print('.')
        i += 1
    return out

a = main(samplesize)
print(pretty(a[0])) #will error here if no solutions found

#pretty print to output file
f = open('%d-%d.txt' % (ndistricts, samplesize), 'w')
for i in a:
    f.write(pretty(i))
    f.write('\n')
f.close()
