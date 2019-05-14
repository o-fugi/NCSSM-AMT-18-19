import numpy as np
import matplotlib.pyplot as plt

# city constants
max_democratic = 0.7
target_integral = 4.822

def power_percent_dem(distance, width, intensity):
    raw_value = 1/pow(distance/width, intensity)
    if(raw_value < max_democratic):
        return raw_value
    else:
        return max_democratic

def return_width(p, int_limits, target_area): #int limits is how far you want to integrate out your city
    a = pow(int_limits, -p+1)/(-p+1)
    b = -1/((-p+1)*pow(max_democratic, (1-p)/p)) + pow(max_democratic, (p-1)/p)
    return find_roots(p, a, b, target_area, 0.01, p*5)

def find_roots(power, a, b, c, min, max): # for ax^p + bx - c = 0
    while(True):
        avg = (min + max)/2
        y_val = a*pow(avg, power)+ b*avg - c
        if(y_val > 0.01):
            max = avg
        elif(y_val < -0.01):
            min = avg
        else:
            return avg

p = 0.95
test_width = return_width(p, 10, 3.0975)
print(pow(test_width, p)*pow(10, -p+1)/(-p+1) + test_width*(-1/((-p+1)*pow(max_democratic, (1-p)/p)) + pow(max_democratic, (p-1)/p)))
