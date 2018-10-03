import cProfile, random

filename = 'house-minvalid.txt'
outputfile = 'supreme-house-by-minvalid'

f = open(filename, 'r')
s = f.readline().strip()
exec('complete = ' + s)
f.close()

COUNTIES = sorted(complete.keys())

transpose = {}
for county in COUNTIES:
    transpose[county] = set()
for x in complete.values():
    for y in x:
        for county in y:
            transpose[county].add(y)

A = {y for x in complete.values() for y in x}

OUTPUT = []
OUTPUTFILE = open('%s.txt' % outputfile, 'w')
I = 0
CUR = 100000

def backtrack(clusters, used, a):
    global I, OUTPUT, OUTPUTFILE, CUR, BEST
    if I >= CUR:
        CUR += 100000
        print(len(OUTPUT), I, len(OUTPUT)/I)
    if len(used) == len(COUNTIES) and clusters not in OUTPUT:
        I += 1
        OUTPUT.append(clusters)
        OUTPUTFILE.write(str(len(clusters)) + '\n')
        for cluster in clusters:
            for county in sorted(cluster)[:-1]:
                OUTPUTFILE.write(str(county) + ', ')
            OUTPUTFILE.write(max(cluster) + '\n')
        OUTPUTFILE.write('\n')
        if len(OUTPUT) % 100 == 0:
            print(len(OUTPUT), BEST, I, len(OUTPUT)/I)
        return [clusters]
    #check if we've failed
    amt = {}
    for county in COUNTIES:
        if county not in used:
            amt[county] = 0
    newclusters = set()
    small = len(COUNTIES)
    for cluster in a:
        for county in cluster:
            if county in used:
                break
        else:
            newclusters.add(cluster)
            if len(cluster) < small:
                small = len(cluster)
            for county in cluster:
                amt[county] += 1
    m = min(amt.values())
    lenc = len(clusters)
    if m == 0:
        I += 1
        if lenc < 24:
            print(' '*len(clusters), '-')
        return []
    elif m == 1: #do forced moves
        county = min(amt.keys(), key=lambda x:amt[x])
        for i in newclusters:
            if county in i:
                out = []
                if lenc < 25:
                    print(' '*(len(clusters) - 1), '#' + str(len(i)))
                for adding in backtrack(clusters.union({i}), used.union(i), newclusters):
                    out.append(adding)
                if lenc < 24 and len(out) == 0:
                    print(' '*len(clusters), '-')
                return out
    #step
    out = []
    if lenc > 0:
        small = max(small, max(len(i) for i in clusters))
    maxlen = max(len(i) for i in newclusters)
    first = small
    while len(out) == 0 and small < maxlen:
        iterator = [i for i in newclusters if len(i) == small]
        if lenc < 25:
            if small > first:
                print(' '*(len(clusters) - 1), '*' + str(small), len(iterator))
            else:
                print(' '*len(clusters), small, len(iterator))
        for i in iterator:
            for adding in backtrack(clusters.union({i}), used.union(i), newclusters):
                out.append(adding)
        small += 1
    if lenc < 24 and len(out) == 0:
        print(' '*len(clusters), '-')
    return out

def main():
    out = backtrack(set(), set(), A)
    return out

#cProfile.run('main()', sort='tottime')
main()
print(len(OUTPUT))
OUTPUTFILE.close()
