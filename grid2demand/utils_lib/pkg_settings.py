# -*- coding:utf-8 -*-
##############################################################
# Created Date: Wednesday, September 6th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################
import os

pkg_settings = {
    # specify required files for grid2demand, and optional files for grid2demand
    "required_files": ["node.csv", "poi.csv"],
    "optional_files": ["zone.csv"],

    # specify required fields for node.csv and poi.csv and zone.csv (optional)
    "node_fields": ["node_id", "x_coord", "y_coord",
                    "activity_type", "is_boundary", "ctrl_type", "poi_id"],
    "poi_fields": ["poi_id", "building", "amenity", "centroid", "area", "geometry"],
    "zone_geometry_fields": ["zone_id", "geometry"],
    "zone_centroid_fields": ["zone_id", "x_coord", "y_coord"],

    # if input data is too large, you can split the input data into chunks and process them separately
    "data_chunk_size": 1000,

    # run the program in parallel mode, if cpu_cores > 1
    "set_cpu_cores": os.cpu_count(),

    # the initial value for trip purpose, usr can add more trip purposes
    "trip_purpose_dict": {1: {"name": 'home-based-work', "alpha": 28507, "beta": -0.02, "gamma": -0.123},
                          2: {"name": 'home-based-other', "alpha": 139173, "beta": -1.285, "gamma": -0.094},
                          3: {"name": 'non-home-based', "alpha": 219113, "beta": -1.332, "gamma": -0.1}
                          },

    # the default trip rate for each POI type and trip purpose
    "poi_purpose_prod_dict": {'library'       : {1: 8.16},  # {trip purpose: trip rate}
                              'university'    : {1: 1.17},
                              'office'        : {1: 2.04},
                              'arts_centre'   : {1: 0.18},
                              'university;yes': {1: 1.17},
                              'bank'          : {1: 12.13},
                              'childcare'     : {1: 11.12},
                              'school'        : {1: 2.04},
                              'public'        : {1: 4.79},
                              'post_office'   : {1: 11.21},
                              'pharmacy'      : {1: 10.29},
                              'yes'           : {1: 1.15}
                              },

    "poi_purpose_attr_dict": {'parking'           : {1: 2.39},
                              'apartments'        : {1: 0.48},
                              'motorcycle_parking': {1: 2.39},
                              'theatre'           : {1: 6.17},
                              'restaurant'        : {1: 7.80},
                              'cafe'              : {1: 36.31},
                              'bar'               : {1: 7.80},
                              'bicycle_parking'   : {1: 2.39},
                              'residential'       : {1: 0.48},
                              'commercial'        : {1: 3.81},
                              'house'             : {1: 0.48},
                              'stadium'           : {1: 0.47},
                              'retail'            : {1: 6.84},
                              'fast_food'         : {1: 14.13},
                              'yes'               : {1: 1.15}
                              }
}
