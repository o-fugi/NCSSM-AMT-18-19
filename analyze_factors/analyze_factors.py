#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import math as m
import sys
import random
from scipy import stats
from matplotlib.animation import FuncAnimation
from voronoi_redistricting import * 
from modified_random_initial_districts import *
from iterating_factors import *
import matplotlib.colors as mcolors


## Code Organization TODOs ##
# Reduce duplicated code between vote-seat charts and analyze factors functions
# Correct >100% Democratic bug?

# Boxes disregards the edges of the district, while random_generate and voronoi take into account location of cities
map_type = "boxes" # should be "random_generate" "boxes" or "voronoi"
show_states = False 
show_boxplots = False 
show_districts = False  

# Constants for generating maps
dist_factor = .7
most_democratic = 1.0
least_democratic = 0.0

# For random_generate map type
num_maps = 1

# For vote-seat curves
a = 0.1
swing_range = np.arange(-a, a, 0.01)

# Helper functions for makeCityDistribution
def wrap(diff, wrap_value):
    if diff < 0:
        diff = diff+wrap_value
    return float(diff)

def norm(diff, norm_value):
    diff = norm_value - m.fabs(diff) if m.fabs(diff)>norm_value/2 else diff
    return diff

def distFromCityWrap(y, x, city_locations, prec_dim_x, prec_dim_y):
    distance = 1000000000000
    for city in city_locations:
        distance = min(distance, m.sqrt(m.pow(norm(x - city[0], prec_dim_x), 2) + m.pow(norm(y-city[1], prec_dim_y), 2)))
    distance = m.pow(distance, dist_factor)
    return distance

def distFromCityNoWrap(y, x, city_locations, prec_dim_x, prec_dim_y):
    distance = 1000000000000
    for city in city_locations:
        distance = min(distance, m.sqrt(m.pow(x - city[0], 2) + m.pow(y-city[1], 2)))
    distance = m.pow(distance, dist_factor)
    return distance

# Returns prec_dim_x * prec_dim_y array of Democratic percentages as a "state"
# States are generated by randomly (or not randomly, depending on the iterating variable) placing cities
# The cities are most Democratic in the center and exponentially decrease in percent Democratic
# More research needs to be done on the actual distribution of Democrats around a city
def makeCityDistribution(iterating_factor, value, city_locations):
    # (num_cities, intensity, target_mean, prec_dim_x, prec_dim_y, city_locations, city_dist_set, city_dist_center, num_cities_set):
    global intensity, target_mean, num_cities, city_dist_center, district_dim_x, district_dim_y, prec_dim_x, prec_dim_y

    if iterating_factor.idx == 0:
        intensity = value
    if iterating_factor.idx == 1:
        target_mean = value
    if iterating_factor.idx == 2:
        num_cities = value
    if iterating_factor.idx == 3:
        city_dist_center = value
        # num_cities = 1
    if iterating_factor.idx == 4:
        district_dim_x = value
        district_dim_y = value
    if iterating_factor.idx == 5:
        prec_dim_x = int(value)
        district_dim_x = int(value / district_dimension_default)
        prec_dim_y = int(precinct_dimension_iterator.default_value)
        num_cities = 1

    print("prec dim x", prec_dim_x, "prec dim y", prec_dim_y)
    print("dist dim x ", district_dim_x, " dist dim y ", district_dim_y)

    percent_dem = np.zeros([prec_dim_y, prec_dim_x])

    if iterating_factor == city_dist_center_iterator:
        city_locations = np.empty([num_cities, 2])
        for city in range(len(city_locations)):
            city_locations[city][0] = int(prec_dim_x - prec_dim_x/2*city_dist_center if city==0 else prec_dim_x/2*city_dist_center)
            city_locations[city][1] = int(prec_dim_y - prec_dim_y/2*city_dist_center if city==0 else prec_dim_y/2*city_dist_center)
    elif iterating_factor == num_cities_iterator:
        city = [0, 0]
        city[0] = random.randint(0, prec_dim_x - 1)
        city[1] = random.randint(0, prec_dim_y - 1)
        city_locations.append(city)
    elif iterating_factor == precinct_dimension_iterator:
        city_locations = np.empty([num_cities, 2])
        city_locations[0] = [int(prec_dim_x/2), int(prec_dim_y/2)]

    print(city_locations)

    if map_type == "voronoi" or map_type == "random_generate":
        for y, row in enumerate(percent_dem):
            for x, column in enumerate(row):
                factor = distFromCityNoWrap(y, x, city_locations, prec_dim_x, prec_dim_y)
                row[x] = m.pow(intensity, factor)
    else:
        for y, row in enumerate(percent_dem):
            for x, column in enumerate(row):
                factor = distFromCityWrap(y, x, city_locations, prec_dim_x, prec_dim_y)
                row[x] = m.pow(intensity, factor)

    percent_dem *= target_mean/np.mean(percent_dem) # TODO: needs work to make sure the percent Democratic doesn't go above 100%. current method is highly flawed
    #percent_dem = sigmoidShift(percent_dem, target_mean - np.mean([percent_dem]), 1)
    # for row in range(len(percent_dem)):
    #     for col in range(len(percent_dem[0])):
    #         percent_dem[row][col] = min(percent_dem[row][col], most_democratic)
    #         percent_dem[row][col] = max(percent_dem[row][col], least_democratic)

    print(np.mean(percent_dem))
    return percent_dem, city_locations

# Returns boxes districting (no regard for location of cities)
# Input of map, output of np.array where every row is a district
def assignDistrictsBoxes(percent_dem, prec_dim_x, prec_dim_y, district_dim_x, district_dim_y):
    print(district_dim_x, district_dim_y, prec_dim_x, prec_dim_y)
    thing = np.zeros(np.shape(percent_dem))
    by_district_arr = np.zeros([int(district_dim_x*district_dim_y), int(prec_dim_x/district_dim_x*prec_dim_y/district_dim_y)]) # each row is one district, each column is one districting
    for num, district in enumerate(by_district_arr): 
        for d, districting in enumerate(district):
            x1 = int(d % (prec_dim_x/district_dim_x) + (num%district_dim_x)*(prec_dim_x/district_dim_x))
            x2 = int(x1 + prec_dim_x/district_dim_x)
            y1 = int(m.floor(d / (prec_dim_y/district_dim_y)) + m.floor(num/district_dim_y)*prec_dim_y/district_dim_y)
            y2 = int(y1 + prec_dim_y/district_dim_y)
            dist_box = np.take(np.take(percent_dem, range(y1, y2), axis=0, mode='wrap'), range(x1, x2), axis=1, mode='wrap')
            district[d] = np.average(dist_box)
    return by_district_arr

# Helper function for assignDistrictsRandom, for translating between different ways of representing districts
def makeStateIntoNodes(state, numDists):
    totalPop = 10000
    groupMemory = []

    for row in range(state.shape[0]):
        for col in range(state.shape[1]):
            nextNode = initialize()
            #prepare centroid
            nextNode.centroid = [row, col]
            #Distinguish the node and the centroids that the node contains
            nextNode.identity = row*state.shape[1] + col
            nextNode.precincts.add(nextNode.identity)
            #find population and area
            #nextNode.population = int(totalPop/(state.shape[0]*state.shape[1])) #int(state[row][col] * totalPop / (state.shape[0]*state.shape[1] / 2)) 
            #print("%dem = ", state[row][col])
            nextNode.population = ((state[row][col]  - 0.5)**3 + 0.5) * (totalPop * 2 / (state.shape[0] * state.shape[1]))
            #print(nextNode.population)
            nextNode.area       = 1

            my_identity = row*state.shape[1] + col
            myNeighbors = set([my_identity - state.shape[1], my_identity + 1, my_identity + state.shape[1], my_identity - 1])
            if(row == 0):
                myNeighbors.remove(my_identity - state.shape[1])
            if(col == 0):
                myNeighbors.remove(my_identity - 1)
            if(row == state.shape[0] - 1):
                myNeighbors.remove(my_identity + state.shape[1])
            if(col == state.shape[1] - 1):
                myNeighbors.remove(my_identity + 1)

            if -1 in myNeighbors:
                myNeighbors.remove(-1)

            nextNode.neighbors.update(myNeighbors)
            groupMemory.append(nextNode)

    idealPop = totalPop/(0.0+numDists)
    return groupMemory, idealPop
    
# Uses Sam Eure's code to generate random districts
# Now corrected for population
def assignDistrictsRandom(state, num_districts):
    groupMemory, idealPop = makeStateIntoNodes(state, num_districts)
    groupList = generateRandomInitialDistricting(groupMemory, num_districts, num_maps, idealPop)

    boxplot_arr = np.zeros([num_maps, num_districts])
    for i, districting in enumerate(groupList): #for map but map is a keyword 
        for d in range(len(districting)): # for district
            for precinct in districting[d].precincts:
                precinct = float(precinct)
                boxplot_arr[i][d] += state[m.floor(precinct/state.shape[1]), int(precinct % state.shape[1])]
            boxplot_arr[i][d] /= len(districting[d].precincts)

    if show_districts:
        district_colorings = np.zeros_like(state)
        for d in range(len(groupList[0])): # for district
            for precinct in districting[d].precincts:
                district_colorings[m.floor(precinct/state.shape[1]), int(precinct % state.shape[1])] = boxplot_arr[0][d]
        plt.imshow((district_colorings), cmap='RdBu', interpolation='nearest')
        plt.show()

    return boxplot_arr.transpose()

# Creates city distribution with some default values and shows the boxplot
def runExample():
    intensity = 0.96
    target_mean = 0.5
    prec_dim_x = 32; prec_dim_y = 32
    district_dim_x = 4; district_dim_y = 4
    num_cities = 5
    num_cities_set = False
    city_dist_set = False
    city_dist_center = 0 

    city_locations = np.empty([num_cities, 2])
    for city in city_locations:
        city[0] = random.randint(0, prec_dim_x - 1)
        city[1] = random.randint(0, prec_dim_y - 1)

    state = makeCityDistribution(num_cities, intensity, target_mean, prec_dim_x, prec_dim_y, city_locations, city_dist_set, city_dist_center, num_cities_set) 
    boxplot_arr = assignDistrictsBoxes(state, prec_dim_x, prec_dim_y, district_dim_x, district_dim_y)

    boxplot_arr = np.sort(boxplot_arr, axis=0)
    organized_medians = [np.median(district) for district in boxplot_arr]
    fig, ax = plt.subplots()
    ax.boxplot(np.transpose(boxplot_arr))

    ax.set_xlabel("district")
    ax.set_ylabel("percent Democratic")
    ax.axis([1, 16, 0.45, 0.55])
    plt.show()

def sigmoidShift(state, c, a):
    return [1/(1+(1/i-1)*np.exp(-4/(1-4/3*pow(i,2))*c)) for i in state]
    return 1/(1+(1/state-1)*np.exp(-4/(1-4*c)))
    return [1/(1+(1/i-1)*np.exp(-4/(1-4*c))) for i in state]


# Runs through an iteration of one variable and plots seats won, linearity of boxplots, etc
def analysisExample():
    seats_won = []
    average_slopes = []
    r_values = []
    slopes_at_50 = [] # slope for middle 50% of districts 
    vc_curves = []
    vc_slopes = []

    # choose which input map factor to change
    iterating_factor = district_num_iterator

    # choose city_locations if they remain constant
    city_locations = []
    if iterating_factor != num_cities_iterator and iterating_factor != city_dist_center_iterator:
        city_locations = np.empty([num_cities, 2])
        for city in city_locations:
            city[0] = random.randint(0, prec_dim_x - 1)
            city[1] = random.randint(0, prec_dim_y - 1)

    # iterate over the map factor
    for value in iterating_factor.iterating_range:
        print(" ****************************************** value = %s" % str(value))
        state, city_locations = makeCityDistribution(iterating_factor, value, city_locations) 
        if show_states:
            fig_state, ax_state = plt.subplots()
            ax_state.imshow((state), cmap='RdBu', interpolation='nearest')
            plt.show()
        # create ensemble
        if map_type == "voronoi":
             boxplot_arr = assignDistrictsVoronoi(state, district_dim_x*district_dim_y, 1)
        elif map_type == "random_generate":
            boxplot_arr = assignDistrictsRandom(state, district_dim_x*district_dim_y)
        else:
            boxplot_arr = assignDistrictsBoxes(state, prec_dim_x, prec_dim_y, district_dim_x, district_dim_y)
        boxplot_arr = np.sort(boxplot_arr, axis=0)
        # these are just used a lot in calculations
        distr_medians = [np.median(district) for district in boxplot_arr]
        # find average slope and r value
        lin_regress = stats.linregress(range(0, len(distr_medians)), distr_medians)
        average_slopes.append(lin_regress.slope)
        r_values.append(lin_regress.rvalue)
        # find slopes at 50
        distr_medians_abbrev = distr_medians[int(len(distr_medians)/4) : int(len(distr_medians)/4*3)]
        lin_regress_abbrev = stats.linregress(range(int(len(distr_medians)/4) + 1, int(len(distr_medians)/4*3) + 1), distr_medians_abbrev)
        slopes_at_50.append(lin_regress_abbrev.slope)
        ##### VOTE SEAT CURVES ########
        swing_votes = []
        for swing in swing_range:
            swing_medians = [0 if (i+swing < 0) else (1 if (i+swing > 1) else i+swing) for i in distr_medians]
            #swing_medians = sigmoidShift(distr_medians,swing, a)
            seats_won_vc = 0
            for num, median in enumerate(swing_medians):
                if median > 0.5:
                    seats_won_vc += 1
            seats_lost = district_dim_x*district_dim_y - seats_won_vc
            if(seats_won_vc != 0) and (seats_lost != 0):
                x = (swing_medians[seats_lost] - 0.5)/(swing_medians[seats_lost] - swing_medians[seats_lost - 1]) # x is the x-distance from the last district lost to the 0.5 mark
            else:
                x = 0
            fractional_won = seats_won_vc + x
            swing_votes.append(fractional_won) # this is a vote-seat curve
            if abs(swing - 0) <= 1e-09:
                seats_won.append(fractional_won)
                print("seats_won = ", seats_won[-1], " out of ", district_dim_x*district_dim_y/2 ) 
        vc_curves.append(swing_votes) #add to the list of vote-seat curves
        # for debugging, create all graphs
        if show_boxplots:
            fig, ax = plt.subplots()
            ax.boxplot(np.transpose(boxplot_arr))
            ax.plot(range(1, len(distr_medians) + 1), [lin_regress.slope * i + lin_regress.intercept for i in range(len(distr_medians))])
            # ax.plot(range(int(len(distr_medians)/4) + 1, int(len(distr_medians)/4*3) + 1), [lin_regress_abbrev.slope * i + lin_regress_abbrev.intercept for i in range(int(len(distr_medians)/4 + 1), int(len(distr_medians)/4*3 + 1))])
            # ax.plot([.5 for i in range(len(distr_medians) + 1)])
            ax.plot(range(1, len(distr_medians) + 1), distr_medians)
            ax.set_xlabel("district")
            # ax.set_ylim([0.2, 1.0])
            ax.set_ylabel("percent Democratic")
            ax.set_title("%s = %s " % (iterating_factor.name, str(value)))
            plt.show()

    # seats_won_avg = np.convolve(seats_won, np.ones((3,))/3, mode='same')

    # vote-seat curves
    fig_vc, ax_vc = plt.subplots()
    normalize = mcolors.Normalize(vmin=min(iterating_factor.iterating_range), vmax=max(iterating_factor.iterating_range))
    colormap = cm.jet
    for i in range(len(vc_curves)):
        ax_vc.plot(swing_range+0.5, vc_curves[i], color=colormap(normalize(iterating_factor.iterating_range[i]))) 
    ax_vc.set_title("Vote Seat Curves for %s" % iterating_factor.name)
    ax_vc.set_ylabel("Votes Won")
    ax_vc.set_xlabel("% Democratic")

    for curve in vc_curves:
        lin_regress_vc = stats.linregress(swing_range, curve)
        vc_slopes.append(lin_regress_vc.slope)

    scalarmappable = cm.ScalarMappable(norm=normalize, cmap=colormap)
    scalarmappable.set_array(iterating_factor.iterating_range)
    cbar = plt.colorbar(scalarmappable)
    cbar.set_label(iterating_factor.name, rotation=270)

    fig, ax = plt.subplots()
    ax1 = plt.subplot(2, 1, 1)
    ax1.set_title("vote seat curve slopes")
    ax1.set_xlabel(iterating_factor.name)
    ax1.set_ylabel("slope")
    #plt.plot(iterating_factor.iterating_range, [i - j for (i, j) in zip(average_slopes, slopes_at_50)])
    plt.plot(iterating_factor.iterating_range, vc_slopes)

    
    ax2 = plt.subplot(2, 1, 2)
    ax2.set_title("difference between actual and expected seats won")
    ax2.set_xlabel(iterating_factor.name)
    ax2.set_ylabel("advantage")
    if iterating_factor == precinct_dimension_iterator:
        plt.plot(iterating_factor.iterating_range, [i - j*district_dim_y/2 for (i, j) in zip(seats_won, range(1, int(prec_dim_x/district_dimension_default)))])
    if iterating_factor == district_num_iterator:
        plt.plot(iterating_factor.iterating_range, [i / (j**2/2) for (i, j) in zip(seats_won, [k**2 for k in district_num_iterator.iterating_range])])
    else:
        plt.plot(iterating_factor.iterating_range, [i / (district_dim_x*district_dim_y/2) for i in seats_won])

    # ax3 = plt.subplot(2, 2, 3)
    # ax3.set_title("seats_won")
    # ax3.set_xlabel(iterating_factor.name)
    # ax3.set_ylabel("number of seats won out of %d" % (district_dim_x*district_dim_y))
    # plt.plot(iterating_factor.iterating_range, seats_won)

    # ax4 = plt.subplot(2, 2, 4)
    # ax4.set_title("slope of near-50% districts")
    # ax4.set_xlabel(iterating_factor.name)
    # ax4.set_ylabel("slope")
    # plt.plot(iterating_factor.iterating_range, slopes_at_50)

    plt.show()

# Creates plot and animation of voteSeatCharts depending on iterator input
def voteSeatCharts(): 
    #outputs
    vc_curves = [] # one vote-seat curve for each intensity

    iterating_factor = city_dist_from_center_iterator 

    city_locations = []
    if iterating_factor != num_cities_iterator and iterating_factor != city_dist_center_iterator:
        city_locations = np.empty([num_cities, 2])
        for city in city_locations:
            city[0] = random.randint(0, prec_dim_x - 1)
            city[1] = random.randint(0, prec_dim_y - 1)

    fig, axes = plt.subplots(nrows=5, ncols=2)
    for value, ax in zip(iterating_factor.iterating_range, axes.flat):
        print(" ****************************************** value = %s" % str(value))
        state, city_locations = makeCityDistribution(iterating_factor, value, city_locations) 
        # create ensemble
        if map_type == "voronoi":
             boxplot_arr = assignDistrictsVoronoi(state, district_dim_x*district_dim_y, 1)
        elif map_type == "random_generate":
            boxplot_arr = assignDistrictsRandom(state, district_dim_x*district_dim_y)
        else:
            boxplot_arr = assignDistrictsBoxes(state, prec_dim_x, prec_dim_y, district_dim_x, district_dim_y)
        boxplot_arr = np.sort(boxplot_arr, axis=0)
        # these are just used a lot in calculations
        distr_medians = [np.median(district) for district in boxplot_arr]
        print("distr_medians = ", distr_medians)
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
        ax.set_title("%s = %s"  % (iterating_factor.name, str(value)))
        ax.plot(swing_range, swing_votes)
        vc_curves.append(swing_votes) #add to the list of vote-seat curves
        # plot the chart
        if show_states:
            fig = plt.figure(1)
            plt.plot(swing_range+.5, swing_votes)
            fig2 = plt.figure(2)
            plt.imshow((state), cmap='RdBu', interpolation='nearest')
            plt.show()

    fig, ax = plt.subplots()
    holder_arr = vc_curves[0]
    vs_chart, = ax.plot(swing_range+0.5, np.arange(0, len(swing_range))*16/12, 'r-', linewidth=2)

    def update(i):
        vs_chart.set_ydata(vc_curves[int(i)])
        return vs_chart, ax
    
    anim = FuncAnimation(fig, update, frames=np.arange(0, len(iterating_factor.iterating_range)))
    plt.tight_layout()
    plt.show()

    
analysisExample()
#voteSeatCharts()
#runExample()
