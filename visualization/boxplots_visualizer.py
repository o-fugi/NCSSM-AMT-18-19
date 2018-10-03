import matplotlib.pyplot as plt

filename = '120-100000.txt'

#read output file
f = open(filename, 'r')
L = [[]]
n = 0
for line in f:
    if line == '\n':
        n += 1
        #if n % 8 == 0:
        #    L.append([])
        L.append([])
    #elif line[0] not in '0123456789' and line[-2] != ',' and line[-1] == '\n':
        pass
    elif ':' in line:
        form = line.replace(':', ',').strip().split(', ')[1:]
        L[-1].append(len(form))
    elif line[-2] == ',' or line[-1] != '\n':
        L.pop()
f.close()
print('Read', n)


D = {}
for i in L:
    for x in set(i):
        c = i.count(x)
        if x in D.keys():
            D[x].append(c)
        else:
            D[x] = [c]

table = [D[x] if x in D.keys() else [] for x in range(1, max(D.keys()))]
plt.boxplot(table)
plt.show()
