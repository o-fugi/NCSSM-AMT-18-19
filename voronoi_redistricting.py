import numpy as np
import matplotlib.pyplot as plt
import random as rand
import math as m
import itertools
import time
from termcolor import colored

area_fudge = 0.4

#input of state map and number of districts
#output of array where every row is a districting and every column is a district
def assignDistrictsVoronoi(state, district_num, desired_districtings):
    districting_list = np.ndarray([desired_districtings, district_num]) #this is the returned list of percent_dem values for each district
    district_count = 0 # number of districtings made so far

    # generate first centroids
    centroid_list = np.empty([district_num, 2])
    state_y, state_x = state.shape
    for centroid in centroid_list: 
        centroid[0] = rand.randint(0, state_x - 1)
        centroid[1] = rand.randint(0, state_y - 1)

    #iterate until area is within area_fudge
    while(district_count < desired_districtings):
        # create array with each point assigned to a centroid
        state_district_assigned = np.empty_like(state)
        for row_idx, row in enumerate(state_district_assigned):
            for col_idx, point in enumerate(row):
                min_dist = 10000000
                point = 1000000
                for index, centroid in enumerate(centroid_list):
                    dist = m.sqrt((centroid[0] - col_idx)**2 + (centroid[1] - row_idx)**2)
                    if min_dist >= dist:
                        state_district_assigned[row_idx][col_idx] = int(index)
                    min_dist = min(dist, min_dist)

        state_district_assigned = state_district_assigned.astype(int)
        print(state_district_assigned)

        adjacencies = []
        for row_idx, row in enumerate(state_district_assigned):
            for col_idx, entry in enumerate(row):
                if col_idx == len(row) - 1:
                    continue
                if entry != state_district_assigned[row_idx][col_idx + 1]:
                    adjacencies.append([entry, state_district_assigned[row_idx][col_idx + 1]])
        adjacencies.sort()
        adjacencies_copy = adjacencies
        adjacencies = list(adjacencies for adjacencies,_ in itertools.groupby(adjacencies))
        # count_list = []
        # for adjacency in adjacencies:
        #     count_list.append(adjacencies_copy.count(adjacency))
        # print("all_adjacencies = ", adjacencies)
        # print(count_list)

        # see if there's already equal area
        success = True
        areas = np.zeros([district_num, 1])
        for row in state_district_assigned:
            for point in row:
                areas[int(point)] += 1
        target_population = state_y * state_x / district_num
        for area in areas:
            if (area <= target_population * (1 - area_fudge)) or (area >= target_population * (1 + area_fudge)):
                success = False
                break

        # if there is, move on!
        if success:
            print(colored("FOUND ONE", "red"))
            for row_idx, row in enumerate(state):
                for col_idx, entry in enumerate(row):
                    districting_list[district_count][state_district_assigned[row_idx][col_idx]] += entry
            for district_idx, district in enumerate(districting_list[district_count]):
                districting_list[district_count][district_idx] /= areas[district_idx]
            district_count += 1
            state_y, state_x = state.shape
            for centroid in centroid_list: 
                centroid[0] = rand.randint(0, state_x - 1)
                centroid[1] = rand.randint(0, state_y - 1)
            break

        # else, choose a random adjacency... 
        adjacency_idx = rand.randint(0, len(adjacencies) - 1)
        # and change all the precincts bordering that adjacency to be a member of the smaller district
        print("adjacencies changed = ", adjacencies[adjacency_idx])
        # pop0 = areas[adjacencies[adjacency_idx][0]]
        # pop1 = areas[adjacencies[adjacency_idx][1]]
        # while(abs(pop0 - pop1) > count_list[adjacency_idx]): 
        #     print("pop0 = ", pop0, " pop1 = ", pop1)
        #     print(count_list[adjacency_idx])
        pop0 = areas[adjacencies[adjacency_idx][0]]
        pop1 = areas[adjacencies[adjacency_idx][1]]
        if pop0 > pop1:
            for row_idx, row in enumerate(state_district_assigned):
                for col_idx, entry in enumerate(row):
                    if col_idx == len(row) - 1:
                        continue
                    if (entry == adjacencies[adjacency_idx][0]) and (state_district_assigned[row_idx][col_idx + 1] == adjacencies[adjacency_idx][1]):
                        state_district_assigned[row_idx][col_idx] = adjacencies[adjacency_idx][1]
        else:
            for row_idx, row in enumerate(state_district_assigned):
                for col_idx, entry in enumerate(row):
                    if col_idx == len(row) - 1:
                        continue
                    if (entry == adjacencies[adjacency_idx][0]) and (state_district_assigned[row_idx][col_idx + 1] == adjacencies[adjacency_idx][1]):
                        state_district_assigned[row_idx][col_idx + 1] = adjacencies[adjacency_idx][0]

        print(state_district_assigned)
                    
        for centroid_index in adjacencies[adjacency_idx]: # for each of the affected districts
            dist_sums = np.full(state.shape, 1000)
            # create a numpy array of sum of distances from that district's points
            for row_idx_ctr, row_ctr in enumerate(state_district_assigned): #iterate through possible centroids
                for col_idx_ctr, entry_ctr in enumerate(row_ctr): #iterate through possible centroids
                    if entry_ctr == centroid_index: #make sure it's actually part of the district
                        dist_sums[row_idx_ctr][col_idx_ctr] = 0
                        for row_idx, row in enumerate(state_district_assigned): #iterate through all members of the district
                            for col_idx, entry in enumerate(row): #iterate through all members of the district
                                if entry == centroid_index: #make sure those points are actually part of the district
                                    dist_sums[row_idx_ctr][col_idx_ctr] += m.sqrt((row_idx - row_idx_ctr)**2 + (col_idx - col_idx_ctr)**2)
            new_centroid = list(np.unravel_index(dist_sums.argmin(), dist_sums.shape))
            new_centroid[0], new_centroid[1] = new_centroid[1], new_centroid[0]
            print("changing centroid for ", centroid_index, " from ", centroid_list[centroid_index], " to ", new_centroid)
            centroid_list[centroid_index] = new_centroid 

state = np.ndarray([16, 16])
for i in range(0, len(state.flat)):
    state.flat[i] = rand.random()

assignDistrictsVoronoi(state, 16, 6)
