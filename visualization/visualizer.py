import matplotlib.pyplot as plt
import networkx as nx

filename = 'house-output-100000.txt'
coordfile = 'nc-seats.txt'

#read output file
f = open(filename, 'r')
L = [[]]
COUNTIES = set()
for line in f:
    if line == '\n':
        L.append([])
    if ':' in line:
        form = line.replace(':', ',').strip()
        L[-1].append(form.split(', ')[1:])
        COUNTIES = COUNTIES.union(set(form.split(', ')[1:]))
COUNTIES = sorted(COUNTIES)
f.close()
print('Read')
weight = 1/len(L)

#init graph
G = nx.Graph()
for county in COUNTIES:
    G.add_node(county)
for county1 in COUNTIES:
    for county2 in COUNTIES:
        if county1 != county2:
            G.add_edge(county1, county2, weight=0)

#graph edge weights
for clusters in L:
    for cluster in clusters:
        for i1 in range(len(cluster) - 1):
            for i2 in range(i1 + 1, len(cluster)):
                G.get_edge_data(cluster[i1], cluster[i2])['weight'] += weight
print('Analyzed')

#coordinate file
pos = {}
labelpos = {}
f = open(coordfile, 'r')
for line in f:
    fmt = line.strip().split(',')
    pos[fmt[0]] = (float(fmt[1]), float(fmt[2]))
    labelpos[fmt[0]] = (float(fmt[1]), float(fmt[2]) + 0.03) #more readable to offset up a bit
f.close()

nx.draw_networkx_nodes(G, pos, node_size=10)

edge_list = []
maxweight = max(G.get_edge_data(c1, c2)['weight'] for c1 in COUNTIES for c2 in COUNTIES if c1 != c2)
for i1 in range(len(COUNTIES) - 1):
    for i2 in range(i1 + 1, len(COUNTIES)):
        edge_list.append((COUNTIES[i1], COUNTIES[i2]))
width = [G.get_edge_data(*edge)['weight'] for edge in edge_list]
#red edges occur 100% of the time
edge_color = ['r' if G.get_edge_data(*edge)['weight'] == maxweight else 'b' for edge in edge_list]
nx.draw_networkx_edges(G, pos, edge_list=edge_list, width=width, edge_color=edge_color)

nx.draw_networkx_labels(G, labelpos, font_size=10)

print('Visualized')
plt.show()
