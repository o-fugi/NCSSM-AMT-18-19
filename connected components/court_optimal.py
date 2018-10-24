import cProfile, random, wrapper, copy
import itertools as it
import timeit

#input
filename = 'reduced-house-minvalid.txt'
outputfile = 'court-optimals2.txt'

f = open(filename, 'r')
s = f.readline().strip()
exec('complete = ' + s)
f.close()

filename = 'county_pop_adjacency.txt' #file containing populations and adjacencies of all counties
ndistricts = 120 #50 for senate, 120 for house
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

for x in complete.keys():
    complete[x] = sorted(complete[x], key=len)

COUNTIES = sorted(complete.keys())

A = {y for x in complete.values() for y in x}

D = {}
S = sorted([set(i) for i in A], key=len)
i = 0
while i < len(S):
    if len(S[i]) in D.keys():
        D[len(S[i])].append(S[i])
    else:
        D[len(S[i])] = [S[i]]
    i += 1

transpose = {}
for county in COUNTIES:
    transpose[county] = set()
for x in complete.values():
    for y in x:
        for county in y:
            transpose[county].add(y)

VAL = {}
for county in COUNTIES:
    VAL[county] = 1 / min(len(i) for i in complete[county])

OUTPUT = []
OUTPUTFILE = open(outputfile, 'w')
I = 0
CUR = 10000
BEST = 0
V = [12] + [len(S)] * (len(S[-1]) - 1)
DONE = [False]*len(S[-1])

def connected_components(s, adjs):
    seen = set()
    def component(node):
        nodes = {node}
        while nodes:
            node = nodes.pop()
            seen.add(node)
            nodes |= adjs[node].intersection(s) - seen
            yield node
    for node in s:
        if node not in seen:
            yield list(component(node))

def flood_valid(used):
    for component in connected_components({a:b for a,b in ADJS.items() if a not in used}):
        pop = sum([POPS[c] for c in component])
        if pop // MINDIST == pop // MAXDIST:
            return False
    return True

def valid(used):
    U = copy.copy(used)
    for c in COUNTIES:
        if c not in U:
            for cluster in complete[c]:
                for c2 in cluster:
                    if c2 in used:
                        break
                else:
                    break
            else:
                COUNTIES.remove(c)
                COUNTIES.insert(0, c)
                return False
            for c2 in cluster:
                U.add(c2)
    return True

def articulation(comp, oldadjs):
    if len(comp) == 0:
        return []
    adjs = {}
    for x in comp:
        adjs[x] = oldadjs[x].intersection(comp)
    A = {}
    B = {}
    i = [0]
    def make(v, parent):
        A[v] = i[0]
        B[v] = i[0]
        i[0] += 1
        nchildren = 0
        for x in adjs[v]:
            if x != parent:
                if x not in A.keys():
                    nchildren += 1
                    for y in make(x, v):
                        yield y
                if B[x] < B[v]:
                    B[v] = A[x]
        if A[v] == 0:
            if nchildren > 1:
                yield v
        elif A[v] == B[v] and nchildren > 0:
            yield v
    for v in comp:
        break
    for out in make(v, None):
        yield out
"""
def backtrack_generator(d, used, cur, target, comp, comp_art):
    global I
    I += 1
    if I % 1000000 == 0:
        print(I)
    newused = used.union(d[cur])
    '''for i in range(len(comp)):
        print(comp[i])
        print(comp_art[i])
        print()'''
    art = {j for i in comp_art for j in i}
    if d[cur].isdisjoint(art):
        newcomp = [list(set(c) - d[cur]) for c in comp]
    else:
        newcomp = list(connected_components({a:b for a,b in ADJS.items() if a not in newused}))
    newcomp_art = []
    for c in newcomp:
        pop = sum([POPS[i] for i in c])
        if pop // MINDIST == pop // MAXDIST:
            break
        newcomp_art.append(list(articulation(c, ADJS)))
    else:
        if target == 1:
            yield [cur]
        else:
            for newcur in range(cur + 1, len(d) - target + 2):
                if d[newcur].isdisjoint(newused):
                    for x in backtrack_generator(d, newused, newcur, target - 1, newcomp, newcomp_art):
                        print([cur] + x)
                        yield [cur] + x

def steps(D):
    baseV = [0, 12, 20] + [min(len(D[i]), (100-12+22*2)//i) for i in sorted(D.keys()) if i > 2]
    print(baseV)
    V = copy.copy(baseV)
    partials = {0:[[]]}
    size = 1
    while size < len(V):
        print(size, V[size], len(partials[size-1]))
        partials[size] = []
        for part in partials[size-1]:
            used = {y for x in part for y in x}
            comp = list(connected_components({a:b for a,b in ADJS.items() if a not in used}))
            comp_art = list(list(articulation(set(c) - used, ADJS)) for c in comp)
            for clusters_ind in backtrack_generator(D[size], used, 0, V[size], comp, comp_art):
                clusters = [D[size][i] for i in clusters_ind]
                if len(partials[size]) == 0:
                    pass#print(len(part + clusters))
                    print(len(part + clusters), str(part+clusters).replace('frozenset(', '').replace(')', ''))
                partials[size].append(part + clusters)
        if len(partials[size]) == 0:
            V[size] -= 1
            if V[size] < 0:
                for i in range(size, len(V)):
                    V[i] = baseV[i]
                    del partials[i]
                size -= 1
                V[size] -= 1
        else:
            size += 1
    return partials[max(partials.keys())]
"""

def better(a, b, table):
    for i in range(min(len(a), len(b))):
        A, B = table[a[i]], table[b[i]]
        if len(A) > len(B):
            return 1
        if len(A) < len(B):
            return -1
    return 0

LOOKUP = {}
BADS = set()
J = 0
K = 0
BEST = 0

def opt(s, c, cur, depth=0):
    global I, LOOKUP, J, K, BEST, BADS
    if c in BADS:
        K += 1
        I += 1
        if I % 100000 == 0:
            print(I, J, K, len(LOOKUP), len(BADS), (J+K)/(J+K+len(LOOKUP)+len(BADS)))
        return []
    if frozenset(c) in LOOKUP.keys():
        J += 1
        I += 1
        if I % 100000 == 0:
            print(I, J, K, len(LOOKUP), len(BADS), (J+K)/(J+K+len(LOOKUP)+len(BADS)))
        return LOOKUP[frozenset(c)]
    size = len(s[cur])
    outer = []
    maxsize = len(s[-1])
    maxlen = len(s)
    while (not outer) and (size <= maxsize):
        while (cur < maxlen) and (len(s[cur]) == size):
            if s[cur].issubset(c):
                newc = c - s[cur]
                outs = [[cur]]
                cc = []
                for c2 in connected_components(newc, ADJS):
                    cc.append(c2)
                    pop = sum(POPS[i] for i in c2)
                    if pop//MINDIST == pop//MAXDIST:
                        I += 1
                        if I % 100000 == 0:
                            print(I, J, K, len(LOOKUP), len(BADS), (J+K)/(J+K+len(LOOKUP)+len(BADS)))
                        break
                else:
                    if depth < 8 and len(s[cur]) <= 2:
                        print(' '*depth, len(s[cur]), *[len(i) for i in sorted(cc, key=len)])
                    for c2 in sorted(cc, key=len):
                        r = opt(s, set(c2), cur+1, depth + (1 if size > 1 else 0))
                        if not r:
                            break
                        newouts = []
                        for x in r:
                            for y in outs:
                                newouts.append(y + x)
                        outs = newouts
                    else:
                        b = better(outs[0], outer[0], s) if outer else 0
                        if b > 0:
                            outer = outs
                        elif b == 0:
                            outer.extend(outs)
            cur += 1
        size += 1
    if outer:
        LOOKUP[frozenset(c)] = outer
    else:
        BADS.add(frozenset(c))
    if outer and len(c) > BEST:
        BEST = len(c)
        print(I, BEST)
    return outer

def main():
    out = opt(S, set(COUNTIES), 0)
    return out


def test(f, a):
    for i in a:
        f(*i)
'''
for i in range(0, 100, 10):
    testdata = [[set(random.sample(COUNTIES, i)), ADJS] for _ in range(10000)]
    testdata2 = [[x[0]] for x in testdata]
    print(i, timeit.timeit('test(articulation, testdata)', 'from __main__ import test, articulation, testdata, COUNTIES', number=1),
             timeit.timeit('test(flood_valid, testdata2)', 'from __main__ import test, flood_valid, testdata2, COUNTIES', number=1))

testdata = [set(random.sample(COUNTIES, i)) for _ in range(1000) for i in range(0, 100, 5)]
print('testing')
cProfile.run('[test(flood_valid, testdata) for _ in range(10)]', sort='tottime')
'''
cProfile.run('r=main()', sort='tottime')
#main()
#print(len(OUTPUT))
#print(OUTPUTFILE.name)
#OUTPUTFILE.close()
