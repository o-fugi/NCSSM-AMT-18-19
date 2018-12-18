import numpy as np
import matplotlib.pyplot as plt

class IteratingFactor:
    def __init__(self, name_, iterating_range_, default_value_, idx_):
        self.name = name_
        self.iterating_range = iterating_range_
        self.default_value = default_value_
        self.idx = idx_

intensity_iterator = IteratingFactor("intensity", np.arange(0.5, 1.0, 0.05), 0.96, 0)
target_mean_iterator = IteratingFactor("target_mean", np.arange(.45, .55, 0.01), 0.5, 1)
num_cities_iterator = IteratingFactor("num_cities", np.arange(1, 10, 1), 2, 2)
city_dist_center_iterator = IteratingFactor("city_dist_center", np.arange(0, 1.0, 0.05), 0, 3)
district_size_iterator = IteratingFactor("district_size", [1, 2, 4, 8, 16], 4, 4)

intensity = intensity_iterator.default_value
target_mean = target_mean_iterator.default_value
num_cities = num_cities_iterator.default_value
district_dim_x = district_size_iterator.default_value
district_dim_y = district_dim_x

precinct_dimension_iterator = IteratingFactor("prec_dim", np.arange(district_dim_x, 128, district_dim_x), 16, 5)

prec_dim_x = precinct_dimension_iterator.default_value
prec_dim_y = prec_dim_x
