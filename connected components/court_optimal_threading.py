import cProfile, random, wrapper, copy
import itertools as it
import time
import threading
            
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
L = []
i = 0
while i < len(S):
    if len(S[i]) in D.keys():
        D[len(S[i])].append(S[i])
    else:
        D[len(S[i])] = [S[i]]
    L.append(len(S[i]))
    i += 1
IND = {a:L.index(a) for a in D.keys()}

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

def better(a, b, table):
    if B is None:
        return 1
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

Q = {}

threadlimit = 200
curkey = 0
conflicts = 0
started = 0
Loops = 0

def master(id_):
    global conflicts, Loops
    loops = 0
    while 1:
        loops += 1
        Loops += 1
        if id_ == 0 and loops % 1 == 0:
            print(loops, Loops//loops, curkey, started/(curkey+1), threading.active_count(), conflicts)
        if threading.active_count() < threadlimit:
            keys = list(Q.keys())
            for choice in sorted(keys)[::-1]:
                try:
                    if Q[choice][0] == 'NEW':
                        t = threading.Thread(target=new, args=Q[choice][1])
                        del Q[choice]
                        t.start()
                        break
                    elif Q[choice][0] == 'PAUSED':
                        if len(Q[choice][1].partial_out) == Q[choice][1].nchildren:
                            t = threading.Thread(target=paused, args=(Q[choice][1],))
                            del Q[choice]
                            t.start()
                            break
                    elif Q[choice][0] == 'SPLIT':
                        if len(Q[choice][1].partial_out) == Q[choice][1].nchildren:
                            t = threading.Thread(target=split, args=(Q[choice][1],))
                            del Q[choice]
                            t.start()
                            break
                except:
                    conflicts += 1
                    continue
                    

class Paused:
    def __init__(self, parent, id_, inp, size, nchildren, partial_out={}):
        self.parent = parent
        self.id = id_
        self.inp = inp
        self.size = size
        self.nchildren = nchildren
        self.partial_out = partial_out

class Split:
    def __init__(self, parent, id_, nchildren, partial_out={}):
        self.parent = parent
        self.id = id_
        self.nchildren = nchildren
        self.partial_out = partial_out

def Return(target_id, from_in, val):
    '''Returns val to target_id, marking it using from_in'''
    Q[target_id][1].partial_out[from_in] = val

def new(out_id, inp, cur):
    global curkey, started
    started += 1
    i = cur + 1
    size = len(S[cur])
    if size > len(inp):
        Return(out_id, cur, [])
        return
    for x in D[size]:
        if x == set(inp):
            Return(out_id, S.index(x), [[x]])
            return
    nchildren = 0
    split_keys = []
    parent_key = curkey
    curkey += 1
    for i in range(cur, len(S)):
        if L[i] > size:
            break
        if S[i].issubset(inp):
            split_key = curkey
            curkey += 1
            split_keys.append(split_key)
            ccs = list(connected_components(set(inp)-S[i], ADJS))
            Q[split_key] = ['UNDEFINED', Split(parent_key, i, len(ccs))]
            for cc in ccs:
                child_key = curkey
                curkey += 1
                Q[child_key] = ['NEW', (split_key, cc, i + 1)]
    Q[parent_key] = ['PAUSED', Paused(out_id, cur, inp, size, nchildren)]
    for key in split_keys:
        Q[key][0] = 'SPLIT'

def paused(obj):
    global curkey, started
    started += 1
    partial_outs = obj.partial_out
    best = None
    out = []
    for i in partial_outs.keys():
        r = better(partial_outs[i][0], best)
        if r == 1:
            out = [[i] + partial_outs[i][j] \
                   for j in range(len(partial_outs[i][j]))]
            best = partial_outs[i][0]
        elif r == 0:
            out.extend([[i] + partial_outs[i][j] \
                        for j in range(len(partial_outs[i][j]))])
    if out:
        Return(obj.parent, obj.id, out)
        return
    elif obj.size == len(obj.inp) or obj.size+1 not in IND.keys():
        Return(obj.parent, obj.id, [])
        return
    key = curkey
    curkey += 1
    Q[key] = ['NEW', (obj.parent, obj.inp, IND[obj.size+1])]

def split(obj):
    global curkey, started
    started += 1
    partial_outs = obj.partial_out
    best = None
    out = []
    for i in it.product(*partial_outs.values()):
        print(partial_outs, i)
        out.append([item for sublist in i for item in sublist])
    Return(obj.parent, obj.id, out)

Q[-1] = ['NEW', (None, COUNTIES, 0)]
for i in range(100):
    mster = threading.Thread(target=master, args=(i,))
    mster.start()
    time.sleep(0.1)


