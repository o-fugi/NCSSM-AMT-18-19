import numpy as np
import matplotlib.pyplot as plt

class IteratingFactor:
    def __init__(self, name_, iterating_range_, default_value_, idx_):
        self.name = name_
        self.iterating_range = iterating_range_
        self.default_value = default_value_
        self.idx = idx_

intensity_iterator = IteratingFactor("City Size", np.arange(0.98, 0.8, -0.02), 0.94, 0)
target_mean_iterator = IteratingFactor("target_mean", np.arange(.45, .55, 0.01), 0.5, 1)
num_cities_iterator = IteratingFactor("num_cities", np.arange(1, 10, 1), 2, 2)
city_dist_center_iterator = IteratingFactor("city_dist_center", np.arange(0.1, 0.8, 0.1), 0, 3)
district_num_iterator = IteratingFactor("district_num", [3, 4, 5, 6, 7, 8, 9], 4, 4)
city_clustering_iterator = IteratingFactor("City Clustering Iterator", np.arange(0.5, 1.0, 0.05), 0, 6)

intensity = intensity_iterator.default_value
target_mean = target_mean_iterator.default_value
num_cities = num_cities_iterator.default_value
district_num_x = district_num_iterator.default_value
district_num_y = district_num_x

precinct_dimension_iterator = IteratingFactor("prec_dim", np.arange(32, 128, 32/district_num_x), 32, 5)

prec_dim_x = precinct_dimension_iterator.default_value
prec_dim_y = prec_dim_x
district_dimension_default = int(precinct_dimension_iterator.default_value / district_num_iterator.default_value)
