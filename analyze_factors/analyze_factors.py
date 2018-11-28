import matplotlib.pyplot as plt
import numpy as np
import math as m
import sys
import random
from scipy import stats
from matplotlib.animation import FuncAnimation
from voronoi_redistricting import * 
from modified_random_initial_districts import *

use_voronoi = False

#constants
dist_factor = .7
most_democratic = .57
num_maps = 5

# helper functions for makeCityDistribution
def wrap(diff, wrap_value):
    if diff < 0:
        diff = diff+wrap_value
    return float(diff)

def norm(diff, norm_value):
    diff = norm_value - m.fabs(diff) if m.fabs(diff)>norm_value/2 else diff
    return diff

def giveDistrict(acount, districting):
    district_x = districting % (prec_dim_x / district_dim_x) #x-offset (how far from 0, 0 is district 1)
    district_y = m.floor(districting / (prec_dim_x/district_dim_x)) #y-offset
    
    x_dim = m.floor(wrap(acount%prec_dim_x - district_x, prec_dim_x) / prec_dim_x * district_dim_x)
    y_dim = m.floor(wrap(m.floor(acount/prec_dim_x) - district_y, prec_dim_y) / prec_dim_y * district_dim_y)

    district = int(x_dim) + int(y_dim*(district_dim_x))
    return district #value from 0 to district_dim**2 - 1

def distFromCity(y, x, city_locations, prec_dim_x, prec_dim_y):
    distance = 1000000000000
    for city in city_locations:
        distance = min(distance, m.sqrt(m.pow(norm(x - city[0], prec_dim_x), 2) + m.pow(norm(y-city[1], prec_dim_y), 2)))
    distance = m.pow(distance, dist_factor)
    return distance

# input of num_cities, intensity, and target_mean, output of map
def makeCityDistribution(num_cities, intensity, target_mean, prec_dim_x, prec_dim_y, city_locations):
    percent_dem = np.zeros([prec_dim_y, prec_dim_x])

    # city_locations = np.empty([num_cities, 2])
    # for city in city_locations:
    #     city[0] = random.randint(0, prec_dim_x - 1)
    #     city[1] = random.randint(0, prec_dim_y - 1)
    
    for y, row in enumerate(percent_dem):
        for x, column in enumerate(row):
            factor = distFromCity(y, x, city_locations, prec_dim_x, prec_dim_y)
            row[x] = m.pow(intensity, factor)

    percent_dem *= target_mean/np.mean(percent_dem)
    return percent_dem

# input of map, output of np.array where every row is a district
def assignDistricts(percent_dem, prec_dim_x, prec_dim_y, district_dim_x, district_dim_y):
    by_district_arr = np.zeros([int(district_dim_x*district_dim_y), int(prec_dim_x/district_dim_x*prec_dim_y/district_dim_y)]) # each row is one district, each column is one districting
    for num, district in enumerate(by_district_arr): 
        for d, districting in enumerate(district):
            x1 = int(d % (prec_dim_x/district_dim_x) + (num%district_dim_x)*(prec_dim_x/district_dim_x))
            x2 = int(x1 + prec_dim_x/district_dim_x)
            y1 = int(m.floor(d / (prec_dim_x/district_dim_x)) + m.floor(num/district_dim_y)*prec_dim_y/district_dim_y)
            y2 = int(y1 + prec_dim_y/district_dim_y)
            dist_box = np.take(np.take(percent_dem, range(y1, y2), axis=0, mode='wrap'), range(x1, x2), axis=1, mode='wrap')
            district[d] = np.average(dist_box)
    return by_district_arr

def makeStateIntoNodes(state):
    totalPop = 10000
    groupMemory = []
    print(state.shape)

    for row in range(state.shape[0]):
        for col in range(state.shape[1]):
            nextNode = initialize()
            #prepare centroid
            nextNode.centroid = [row, col]
            #Distinguish the node and the centroids that the node contains
            nextNode.identity = row*state.shape[1] + col
            nextNode.precincts.add(nextNode.identity)
            #find population and area
            nextNode.population += int(state[row][col] * totalPop / (state.shape[0]*state.shape[1] / 2)) 
            nextNode.area       += 1

            my_identity = row*state.shape[1] + col
            myNeighbors = set([my_identity - state.shape[1], my_identity + 1, my_identity + state.shape[1], my_identity - 1])

            if -1 in myNeighbors:
                myNeighbors.remove(-1)

            nextNode.neighbors.update(myNeighbors)
            groupMemory.append(nextNode)

    idealPop = totalPop/(0.0+numDists)
    return groupMemory, idealPop
    
def assignDistrictsRandom(state, num_districts):
    groupMemory, idealPop = makeStateIntoNodes(state)
    groupList = generateRandomInitialDistricting(groupMemory, num_districts, num_maps, idealPop)
    boxplot_arr = np.zeros([num_maps, num_districts])
    for m in range(len(groupList)): #for map but map is a keyword 
        for d in range(len(districting)): # for district
            for precinct in districting[d].precincts:
                boxplot_arr[m][d] += state[m.floor(precinct/state.shape[1]), precinct%state.shape[1]]
            boxplot_arr[m][d] /= len(districting[d].precincts)

    return boxplot_arr.transpose()

def runExample():
    state = makeCityDistribution(5, 0.96, 0.5, 64, 64) 
    boxplot_arr = assignDistricts(state, 64, 64, 4, 4)

    boxplot_arr = np.sort(boxplot_arr, axis=0)
    organized_medians = [np.median(district) for district in boxplot_arr]
    fig, ax = plt.subplots()
    ax.boxplot(np.transpose(boxplot_arr))

    ax.set_xlabel("district")
    ax.set_ylabel("percent Democratic")
    ax.axis([1, 16, 0.45, 0.55])
    plt.show()

def sigmoidShift(state, c, a):
    return [1/(1+(1/i-1)*np.exp(-4/(1-4/3*pow(a,2))*c)) for i in state]

def analysisExample():
    #inputs
    intensity = 0.96
    target_mean = 0.5
    prec_dim_x = 32; prec_dim_y = 32
    district_dim_x = 4; district_dim_y = 4
    num_cities = 2

    #outputs
    seats_won = []
    average_slopes = []
    r_values = []
    slopes_at_50 = [] # slope when districts transition from one party to the other

    intensity_range = np.arange(0.05, 1.0, 0.05)
    cities_range = np.arange(1, 10, 1)
    if(district_dim_x == district_dim_y):
        prec_dim_x_range = np.arange(district_dim_x, prec_dim_y, district_dim_x)

    iterator_range = intensity_range 
    iterator_string = "intensities"

    city_locations = np.empty([num_cities, 2])
    for city in city_locations:
        city[0] = random.randint(0, prec_dim_x - 1)
        city[1] = random.randint(0, prec_dim_y - 1)

    for intensity in iterator_range:
        print(intensity)
        # create simulated state
        state = makeCityDistribution(num_cities, intensity, target_mean, prec_dim_x, prec_dim_y, city_locations) 
        # create ensemble
        # if use_voronoi:
        #     boxplot_arr = assignDistrictsVoronoi(state, 16, 1)
        # else:
        #     boxplot_arr = assignDistricts(state, prec_dim_x, prec_dim_y, district_dim_x, district_dim_y)
        if True:
            boxplot_arr = assignDistrictsRandom(state, 16)
        boxplot_arr = np.sort(boxplot_arr, axis=0)
        # these are just used a lot in calculations
        distr_medians = [np.median(district) for district in boxplot_arr]
        # find seats won
        seats_lost = 0
        for num, median in enumerate(distr_medians):
            if median > 0.5:
                seats_lost = num
                break
        x = (0.5 - distr_medians[seats_lost - 1])/(distr_medians[seats_lost] - distr_medians[seats_lost - 1])
        seats_won.append(district_dim_x*district_dim_y - seats_lost + (1 - x))
        # find average slope and r value
        lin_regress = stats.linregress(range(0, len(distr_medians)), distr_medians)
        average_slopes.append(lin_regress.slope)
        r_values.append(lin_regress.rvalue)
        # find slopes at 50
        slopes_at_50.append(distr_medians[seats_lost] - distr_medians[seats_lost - 1])
        # for debugging, create all graphs
        # plt.imshow((state), cmap='RdBu', interpolation='nearest')
        # plt.show()

    ax1 = plt.subplot(2, 2, 1)
    ax1.set_title("average slopes")
    ax1.set_xlabel(iterator_string)
    ax1.set_ylabel("average boxplot slope")
    plt.plot(iterator_range, average_slopes)
    
    ax2 = plt.subplot(2, 2, 2)
    ax2.set_title("r_values")
    ax2.set_xlabel(iterator_string)
    ax2.set_ylabel("R value")
    plt.plot(iterator_range, r_values)

    ax3 = plt.subplot(2, 2, 3)
    ax3.set_title("seats_won")
    ax3.set_xlabel(iterator_string)
    ax3.set_ylabel("number of seats won out of %d" % (district_dim_x*district_dim_y))
    plt.plot(iterator_range, seats_won)

    ax4 = plt.subplot(2, 2, 4)
    ax4.set_title("slope of near-50% districts")
    ax4.set_xlabel(iterator_string)
    ax4.set_ylabel("slope")
    plt.plot(iterator_range, slopes_at_50)

    plt.show()

def voteSeatCharts():
    #constants
    a = 0.1
    swing_range = np.arange(-a, a, 0.01)

    #inputs
    intensity = 0.96
    target_mean = 0.5
    prec_dim_x = 32; prec_dim_y = 32
    district_dim_x = 4; district_dim_y = 4
    num_cities = 1

    #outputs
    vc_curves = [] # one vote-seat curve for each intensity

    intensity_range = np.arange(0.9, 1.0, 0.01)
    cities_range = np.arange(1, 10, 1)
    if(district_dim_x == district_dim_y):
        prec_dim_x_range = np.arange(district_dim_x, prec_dim_y, district_dim_x)

    iterator_range = intensity_range
    iterator_string = "intensity"

    fig, axes = plt.subplots(nrows=5, ncols=2)
    for intensity, ax in zip(iterator_range, axes.flat):
        # create simulated state
        state = makeCityDistribution(num_cities, intensity, target_mean, prec_dim_x, prec_dim_y) 
        # create ensemble
        if use_voronoi:
            boxplot_arr = assignDistrictsVoronoi(state, 16, 1)
        else:
            boxplot_arr = assignDistricts(state, prec_dim_x, prec_dim_y, district_dim_x, district_dim_y)
        boxplot_arr = np.sort(boxplot_arr, axis=0)
        # these are just used a lot in calculations
        distr_medians = [np.median(district) for district in boxplot_arr]
        # find seats won
        swing_votes = []
        for swing in swing_range:
            swing_medians = sigmoidShift(distr_medians,swing, a)
            seats_won = 0
            for num, median in enumerate(swing_medians):
                if median > 0.5:
                    seats_won += 1
            seats_lost = district_dim_x*district_dim_y - seats_won
            if(seats_won != 0) and (seats_lost != 0):
                x = (swing_medians[seats_lost] - 0.5)/(swing_medians[seats_lost] - swing_medians[seats_lost - 1]) # x is the x-distance from the last district lost to the 0.5 mark
            else:
                x = 0
            fractional_won = seats_won + x
            swing_votes.append(fractional_won) # this is a vote-seat curve
        ax.set_ylabel("votes won")
        ax.set_title("intensity = %f" % intensity)
        ax.plot(swing_range, swing_votes)
        vc_curves.append(swing_votes) #add to the list of vote-seat curves
        # plot the chart
        # fig = plt.figure(1)
        # plt.plot(swing_range+.5, swing_votes)
        # fig2 = plt.figure(2)
        # plt.imshow((state), cmap='RdBu', interpolation='nearest')
        # plt.show()

    fig, ax = plt.subplots()
    holder_arr = vc_curves[0]
    vs_chart, = ax.plot(swing_range+0.5, np.arange(0, len(swing_range))*16/12, 'r-', linewidth=2)

    def update(i):
        vs_chart.set_ydata(vc_curves[int(i)])
        return vs_chart, ax
    
    anim = FuncAnimation(fig, update, frames=np.arange(0, len(iterator_range)))
    plt.tight_layout()
    plt.show()

    
analysisExample()
#voteSeatCharts()
