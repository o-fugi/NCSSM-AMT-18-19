import cProfile, random

filename = 'house-minvalid.txt'
outputfile = 'house-by-minvalid'
frac = 0
taper = 5
minimum = 37

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
OUTPUTFILE = open('%s-%d-%d-%d.txt' % (outputfile, round(1/frac if frac > 0 else 0), minimum, taper), 'w')
I = 0
CUR = 10000
BEST = 0

def backtrack(clusters, used, a):
    global I, OUTPUT, OUTPUTFILE, CUR, BEST
    I += 1
    if I >= CUR:
        CUR += 10000
        print(len(OUTPUT), BEST, I, len(OUTPUT)/I)
    if len(clusters) + len(COUNTIES) - len(used) < minimum:
        return []
    if len(used) == len(COUNTIES) and clusters not in OUTPUT:
        OUTPUT.append(clusters)
        OUTPUTFILE.write(str(len(clusters)) + '\n')
        for cluster in clusters:
            for county in sorted(cluster)[:-1]:
                OUTPUTFILE.write(str(county) + ', ')
            OUTPUTFILE.write(max(cluster) + '\n')
        OUTPUTFILE.write('\n')
        if len(OUTPUT) % 100 == 0:
            print(len(OUTPUT), BEST, I, len(OUTPUT)/I)
        if len(clusters) > BEST:
            BEST = len(clusters)
        return [clusters]
    amt = {}
    for county in COUNTIES:
        if county not in used:
            amt[county] = 0
    newclusters = set()
    for cluster in a:
        for county in cluster:
            if county in used:
                break
        else:
            newclusters.add(cluster)
            for county in cluster:
                amt[county] += 1
    county = min(amt.keys(), key=lambda x:amt[x])
    length = min(amt[county], max(int(amt[county]*frac)+1, taper-len(clusters), 2))
    if len(clusters) < 10:
        print(' '*len(clusters), len(clusters), len(used), county, length)
    if amt[county] > 0:
        I -= 1
        out = []
        y = [x for x in newclusters if county in x]
        for possible in sorted(y, key=len)[:length]:
            for adding in backtrack(clusters.union({possible}), used.union(possible), newclusters):
                if adding not in out:
                    out.append(adding)
        return out
    return []

def main():
    out = backtrack(set(), set(), A)
    return out

#cProfile.run('main()', sort='tottime')
main()
print(len(OUTPUT))
OUTPUTFILE.close()
