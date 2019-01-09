import networkx as nx
import numpy as np
from scipy import sparse
import random
import matplotlib.pyplot as plt
import copy
import cProfile

fs = frozenset

def wilsons(G):
    nodes = list(G.nodes)
    v1 = random.choice(nodes)
    v2 = random.choice(nodes)
    V = [v1]
    v = v1
    while v != v2:
        v = random.choice(list(G.neighbors(v)))
        if v in V:
            V = V[0:V.index(v)]
        V.append(v)

    out = nx.Graph()
    out.add_node(V[-1])
    for i in range(len(V)-1):
        out.add_node(V[i])
        out.add_edge(V[i+1], V[i])
    U = set(V)

    nnodes = len(nodes)
    while len(out.nodes) < nnodes:
        v = random.choice(nodes)
        V = [v]
        while v not in U:
            v = random.choice(list(G.neighbors(v)))
            if v in V:
                V = V[0:V.index(v)]
            V.append(v)
        U.update(set(V))
        for i in range(len(V) - 1):
            out.add_node(V[i])
            out.add_edge(V[i+1], V[i])
    return out

def nspanning(G):
    L = nx.laplacian_matrix(G).toarray()
    return np.linalg.det(L[1:,1:])

def good_edges(G, pops, ndistricts, minpop=None, maxpop=None, err=0.05): #not as fast as possible, but good enough
    if minpop is None or maxpop is None:
        pop = sum(pops.values())
        minpop = int(pop / ndistricts * (1 - err)) + 1
        maxpop = int(pop / ndistricts * (1 + err))

    #heights (orient tree)
    G2 = G.copy()
    H = {}
    height = 1
    todo = {v for v in G2.nodes if G2.degree(v) == 1} #leaves
    while todo:
        possible = set()
        for v in todo:
            for e in G2.edges(v):
                H[fs(e)] = height
            possible.update(set(G.neighbors(v)))
        G2.remove_nodes_from(todo)
        todo = {v for v in possible if v in G2.nodes and G2.degree(v) == 1} #new leaves
        height += 1

    #weights (find good edge sets)
    T = 0
    W = {}
    returning = set()
    for e in sorted(G.edges, key=lambda e:H[fs(e)]):
        W[fs(e)] = {}
        if H[fs(e)] == 1:
            for v in e:
                if G.degree(v) == 1:
                    break
            W[fs(e)][fs()] = pops[v]
            T += 1
            if minpop <= pops[v] <= maxpop:
                W[fs(e)][fs({e})] = 0
                T += 1
        else:
            cur = {fs():0} #generate product
            for e2 in G.edges(list(e)):
                if fs(e2) in W.keys() and e2 != e:
                    newcur = {}
                    for (a,b) in cur.items():
                        for (L,P) in W[fs(e2)].items():
                            for v in e:
                                if v in e2:
                                    break
                            newcur[a.union(L)] = b + P + pops[v]
                    cur = newcur
            for (a,b) in cur.items(): #test items
                if minpop <= b <= maxpop:
                    W[fs(e)][a.union({e})] = 0
                    T += 1
                    if len(a) == ndistricts - 2:
                        returning.add(a.union(fs({e})))
                if b <= maxpop:
                    W[fs(e)][a] = b
                    T += 1
        if T > 5*10**5:
            print('>', end='')
            break
    return returning

def testcode1(n=10): #test wilsons
    pops = {}
    G = nx.Graph()
    for x in range(n):
        for y in range(n):
            G.add_node((x,y))
            if x > 0 and ((x+2*y) % 4 or y == 0 or y == n-1):
                G.add_edge((x,y),(x-1,y))
            if y > 0 and ((x+y) % 3 or x == 0 or x == n-1):
                G.add_edge((x,y),(x,y-1))
            pops[(x,y)] = random.randint(100,200)
    widths = {frozenset(e):0 for e in G.edges}
    works = {frozenset(e):0 for e in G.edges}
    i = 0
    while i < 100:
        i += 1
        print(i, end='')
        G2 = wilsons(G)
        print('.')
        #suuuper inefficient good edge finder in O(VE).
        #O(V+E) is easy, and some form of binary search could probably get close to O(log(E)).
        #   note from future self: O(V+E) was not as easy as I thought.
        #   also O(log(E)) is only possible if the tree structure is already "oriented" (which takes O(V+E) anyway).
        #     and I'm not sure if it is possible, but this isn't the limiting step so I don't care.
        MINDIST = int(sum(pops.values()) / 2 * 0.90) + 1
        MAXDIST = int(sum(pops.values()) / 2 * 1.10)
        for edge in G2.edges:
            G2p = copy.deepcopy(G2)
            G2p.remove_edge(*edge)
            L = list(sum(pops[v] for v in g) for g in nx.connected_components(G2p))
            widths[frozenset(edge)] += abs(L[0]-L[1])
            '''if not (MINDIST < sum(pops[node] for node in cc) < MAXDIST):
                    break
            else:
                #color = 'r'
                #for cc in nx.connected_components(G2p):
                #    nx.draw_networkx(G2p.subgraph(cc), pos={(x,y):(x,y) for x in range(200) for y in range(200)}, with_labels=False,
                #                     edge_color=color, node_size=[pops[k]/10 for k in G2.nodes])
                #    color = 'b'
                #plt.show()'''
            if all(MINDIST < x < MAXDIST for x in L):
                works[frozenset(edge)] += 1
    cutoff = sorted(works.values(), reverse=True)[len(works) // 20]
    works = [i for i in works.keys() if works[i] >= cutoff]
    works = [tuple(e) if tuple(e) in G.edges else tuple(e)[::-1] for e in works]
    s = sum(pops.values())
    m = min(widths.values())
    M = max(widths.values())
    nx.draw_networkx(G, pos={(x,y):(x,y) for x in range(n) for y in range(n)}, node_size=[pops[k]/5 for k in G.nodes],
                     with_labels=False, width=[max(0.1,10*(M-widths[frozenset(e)])/(M-m)) for e in G.edges])
    nx.draw_networkx(G, pos={(x,y):(x,y) for x in range(n) for y in range(n)}, node_size=0,
                     with_labels=False, edgelist=works, width=[max(0.1,10*(M-widths[frozenset(e)])/(M-m)) for e in works], edge_color='r')

    plt.show()

def testcode2(n=20): #all the pieces of a full working example
    pops = {}
    G = nx.Graph()
    for x in range(n):
        for y in range(n):
            G.add_node((x,y))
            if x > 0 and ((x+2*y) % 4 or y == 0 or y == n-1):
                G.add_edge((x,y),(x-1,y))
            if y > 0 and ((x+y) % 3 or x == 0 or x == n-1):
                G.add_edge((x,y),(x,y-1))
            pops[(x,y)] = random.randint(100,200)
    #print(nspanning(G))
    for _ in range(10):
        G2 = wilsons(G)
        for i in [2]:
            g = list(good_edges(G2, pops, i))
            if g:
                e = random.choice(g)
                G2.remove_edges_from(e)
                for cc in nx.connected_components(G2):
                    nspanning(G.subgraph(cc))
    #nx.draw_networkx(G2, pos={(x,y):(x,y) for x in range(n) for y in range(n)},
    #                 node_size=0, with_labels=False)
    #plt.show()

def testcode3(n=50): #optimizing wilsons; written after discovering wilsons was the slow step
    pops = {}
    G = nx.Graph()
    for x in range(n):
        for y in range(n):
            G.add_node((x,y))
            if x > 0 and ((x+2*y) % 4 or y == 0 or y == n-1):
                G.add_edge((x,y),(x-1,y))
            if y > 0 and ((x+y) % 3 or x == 0 or x == n-1):
                G.add_edge((x,y),(x,y-1))
            pops[(x,y)] = random.randint(100,200)
    for _ in range(20):
        G2 = wilsons(G)

#cProfile.run('testcode2()', sort='tottime')
