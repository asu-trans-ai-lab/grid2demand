# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 4th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import os
import pandas as pd
import numpy as np
import math
import csv
import re
import locale
import sys
from pprint import pprint
from collections import defaultdict
import logging
import random
from random import choice


"""PART 3  TRIP GENERATION"""
g_trip_purpose = 0 # comments: this set of global variables are used in the following part 3
g_poi_type_list = []
g_poi_prod_rate_list = []
g_poi_attr_rate_list = []
g_poi_prod_rate_notes_list = []
g_poi_attr_rate_notes_list = []
g_node_prod_list = []
g_node_attr_list = []
g_undefined_prod_rate_poi_name_list = []
g_undefined_attr_rate_poi_name_list = []
g_poi_type_prod_rate_dict = {}
g_poi_type_attr_rate_dict = {}
g_poi_prod_rate_flag = {}
g_poi_attr_rate_flag = {}
g_poi_purpose_prod_dict = defaultdict(defaultdict)
g_poi_purpose_attr_dict = defaultdict(defaultdict)
trip_purpose_list = [1, 2, 3]
g_number_of_unmatched_poi_production_rate = 0
g_number_of_unmatched_poi_attraction_rate = 0


def GetPoiTripRate(trip_rate_folder=None,
                   trip_purpose=None):
    logger.debug("Starting GetPOITripRate")
    global g_poi_purpose_prod_dict
    global g_poi_purpose_attr_dict
    global g_poi_type_list
    global g_undefined_prod_rate_poi_name_list
    global g_undefined_attr_rate_poi_name_list
    global g_poi_type_prod_rate_dict
    global g_poi_type_attr_rate_dict
    global g_trip_purpose
    global g_output_folder
    global g_number_of_unmatched_poi_production_rate
    global g_number_of_unmatched_poi_attraction_rate

    if trip_rate_folder:
        trip_rate_filepath = os.path.join(trip_rate_folder, 'poi_trip_rate.csv')
    else:
        trip_rate_filepath = 'poi_trip_rate.csv'

    # define production/attraction rates of each land use type and trip purpose
    try:
        # user can customize poi_trip_rate.csv in advance
        with open(trip_rate_filepath, errors='ignore') as fp:
            reader = csv.DictReader(fp)
            for line in reader:
                poi_type = line['building']
                for i in trip_purpose_list:
                    try:
                        g_poi_purpose_prod_dict[poi_type][i] = float(line['production_rate' + str(i)])
                    except:
                        g_poi_purpose_prod_dict[poi_type][i] = 0
                    try:
                        g_poi_purpose_attr_dict[poi_type][i] = float(line['attraction_rate' + str(i)])
                    except:
                        g_poi_purpose_attr_dict[poi_type][i] = 0

    except:
        # print('Warning: The folder of poi_trip_rate.csv is NOT defined! Default values will be used...')
        logger.warning('poi_trip_rate.csv does not exist in the current folder. Default values will be used.')
        # default trip generation rates refer to ITE Trip Generation Manual, 10t Edition
        # https://www.troutdaleoregon.gov/sites/default/files/fileattachments/public_works/page/966/ite_land_use_list_10th_edition.pdf
        # unit of measure for all poi nodes is 1,000 SF GFA in this version
        g_poi_purpose_prod_dict = {'library': {trip_purpose_list[0]: 8.16}, 'university': {trip_purpose_list[0]: 1.17},
                                   'office': {trip_purpose_list[0]: 2.04}, 'arts_centre': {trip_purpose_list[0]: 0.18},
                                   'university;yes': {trip_purpose_list[0]: 1.17},
                                   'bank': {trip_purpose_list[0]: 12.13}, 'childcare': {trip_purpose_list[0]: 11.12},
                                   'school': {trip_purpose_list[0]: 2.04},
                                   'public': {trip_purpose_list[0]: 4.79}, 'post_office': {trip_purpose_list[0]: 11.21},
                                   'pharmacy': {trip_purpose_list[0]: 10.29}, 'yes': {trip_purpose_list[0]: 1.15}}

        g_poi_purpose_attr_dict = {'parking': {trip_purpose_list[0]: 2.39}, 'apartments': {trip_purpose_list[0]: 0.48},
                                   'motorcycle_parking': {trip_purpose_list[0]: 2.39},
                                   'theatre': {trip_purpose_list[0]: 6.17}, 'restaurant': {trip_purpose_list[0]: 7.80},
                                   'cafe': {trip_purpose_list[0]: 36.31}, 'bar': {trip_purpose_list[0]: 7.80},
                                   'bicycle_parking': {trip_purpose_list[0]: 2.39},
                                   'residential': {trip_purpose_list[0]: 0.48},
                                   'commercial': {trip_purpose_list[0]: 3.81}, 'house': {trip_purpose_list[0]: 0.48},
                                   'stadium': {trip_purpose_list[0]: 0.47}, 'retail': {trip_purpose_list[0]: 6.84},
                                   'fast_food': {trip_purpose_list[0]: 14.13},
                                   'yes': {trip_purpose_list[0]: 1.15}}

    # Get POI production/attraction rates of each poi type with a specific trip purpose
    if trip_purpose is None:
        # print('Warning: Trip purpose is not defined! Default trip purpose is Purpose 1.')
        logger.warning('Trip purpose is not defined! Default trip purpose is Purpose 1.')
        trip_purpose = trip_purpose_list[0]  # default trip purpose is Purpose 1
        g_trip_purpose = trip_purpose
    else:
        g_trip_purpose = trip_purpose

    poi_id = [poi.id for poi in g_poi_list]
    poi_type = [poi.type for poi in g_poi_list]

    for i in range(len(poi_id)):
        # define production rate of each poi type
        if (poi_type[i] in g_poi_purpose_prod_dict):
            production_rate = g_poi_purpose_prod_dict[poi_type[i]][trip_purpose]
            g_poi_type_prod_rate_dict[poi_type[i]] = production_rate
            g_poi_prod_rate_flag[poi_type[i]] = 1  # comments: the poi type production rate is obtained from the input table
        else:
            g_poi_type_prod_rate_dict[poi_type[i]] = 0.1  # comments: define default value of production rate
            g_poi_prod_rate_flag[poi_type[i]] = 0  # comments: the poi type production rate does not exist in the input table
            g_number_of_unmatched_poi_production_rate += 1
            if poi_type[i] not in g_undefined_prod_rate_poi_name_list:
                # print(g_undefined_trip_rate_poi_name_list)
                g_undefined_prod_rate_poi_name_list.append(poi_type[i])
                logger.info(
                    'The POI production rate of ' + "'" + str(poi_type[i]) + "'" +
                    ' is NOT defined! Default production rate is 0.1.')

        # define attraction rate of each poi type
        if (poi_type[i] in g_poi_purpose_attr_dict):
            attraction_rate = g_poi_purpose_attr_dict[poi_type[i]][trip_purpose]
            g_poi_type_attr_rate_dict[poi_type[i]] = attraction_rate
            g_poi_attr_rate_flag[poi_type[i]] = 1  # comments: the poi type attraction rate is obtained from the input table
        else:
            g_poi_type_attr_rate_dict[poi_type[i]] = 0.1  # comments: define default value of attraction rate
            g_poi_attr_rate_flag[poi_type[i]] = 0  # comments: the poi type attraction rate does not exist in the input table
            g_number_of_unmatched_poi_attraction_rate += 1
            if poi_type[i] not in g_undefined_attr_rate_poi_name_list:
                g_undefined_attr_rate_poi_name_list.append(poi_type[i])
                logger.info(
                    'The POI attraction rate of ' + "'" + str(poi_type[i]) + "'" +
                    ' is NOT defined! Default production rate is 0.1.')

    print('\nTab of trip purposes used in grid2demand = ', g_trip_purpose)
    print('\nTotal number of poi nodes with unmatched production rate = ', g_number_of_unmatched_poi_production_rate)
    print('Total number of poi nodes with unmatched attraction rate = ', g_number_of_unmatched_poi_attraction_rate)
    logger.info('Tab of trip purpose used in grid2demand = ' + str(g_trip_purpose))
    logger.info('Total number of poi nodes with unmatched production rates = ' + str(
        g_number_of_unmatched_poi_production_rate))
    logger.info('Total number of poi nodes with unmatched attraction rates = ' + str(
        g_number_of_unmatched_poi_attraction_rate))

    # create poi_trip_rate.csv
    poi_type = [poi.type for poi in g_poi_list]
    g_poi_type_list = list(set(poi_type))  # comments: obtain unique poi types

    data_index = [i for i in range(len(g_poi_type_list))]
    data_rate = pd.DataFrame(data_index)
    data_rate.columns = ["poi_type_id"]

    data_type = [building for building in g_poi_type_list]
    data_rate['building'] = pd.DataFrame(data_type)

    data_rate['unit_of_measure'] = pd.DataFrame(['1,000 Sq. Ft. GFA'] * len(g_poi_type_list))

    data_rate['trip_purpose'] = pd.DataFrame([g_trip_purpose] * len(g_poi_type_list))

    for item in g_poi_type_list:
        g_poi_prod_rate_list.append(g_poi_type_prod_rate_dict[item])
        g_poi_attr_rate_list.append(g_poi_type_attr_rate_dict[item])
        g_poi_prod_rate_notes_list.append(g_poi_prod_rate_flag[item])
        g_poi_attr_rate_notes_list.append(g_poi_attr_rate_flag[item])

    data_rate['production_rate' + str(g_trip_purpose)] = pd.DataFrame(g_poi_prod_rate_list)

    data_rate['attraction_rate' + str(g_trip_purpose)] = pd.DataFrame(g_poi_attr_rate_list)

    data_rate['production_notes'] = pd.DataFrame(g_poi_prod_rate_notes_list)
    data_rate['attraction_notes'] = pd.DataFrame(g_poi_attr_rate_notes_list)

    # print(data_rate)
    if g_output_folder is not None:
        triprate_filepath = os.path.join(g_output_folder, 'poi_trip_rate.csv')
        data_rate.to_csv(triprate_filepath, index=False, line_terminator='\n')
    else:
        data_rate.to_csv('poi_trip_rate.csv', index=False, line_terminator='\n')

    logger.debug('Ending GetPOITripRate')


def GetNodeDemand(residential_production = None, residential_attraction = None,
                  boundary_production = None, boundary_attraction = None):
    logger.debug('Starting GetNodeDemand')
    global g_node_prod_list
    global g_node_attr_list
    global g_node_list
    global g_output_folder

    if residential_production is None:
        logger.warning('Production value of residential nodes is not defined! Default value is 10.')
        residential_production = 10  # comments: default value if no given latitude
    if residential_attraction is None:
        logger.warning('Attraction value of residential nodes is not defined! Default value is 10.')
        residential_attraction = 10  # comments: default value if no given latitude
    if boundary_production is None:
        logger.warning('Production value of boundary nodes is not defined! Default value is 1000.')
        boundary_production = 1000  # comments: default value if no given latitude
    if boundary_attraction is None:
        logger.warning('Attraction value of boundary nodes is not defined! Default value is 1000.')
        boundary_attraction = 1000  # comments: default value if no given latitude

    # calculate production/attraction values of each node
    log_flag = 0
    for node in g_node_list:
        if node.activity_location_tab == 'residential':   # residential node
            g_node_prod_list.append(residential_production)  # comments: default production value of residential node
            node.production = residential_production
            g_node_attr_list.append(residential_attraction)  # comments: default attraction value of residential node
            node.attraction = residential_attraction

        elif node.activity_location_tab == 'boundary':   # boundary node
            g_node_prod_list.append(boundary_production)  # comments: default production value of boundary node
            node.production = boundary_production
            g_node_attr_list.append(boundary_attraction)  # comments: default attraction value of boundary node
            node.attraction = boundary_attraction

        elif node.activity_location_tab == 'poi':   # poi node
            # define production value of each poi node
            if (int(float(node.poi_id)) in g_poi_id_type_dict.keys()):
                node_poi_type = g_poi_id_type_dict[int(float(node.poi_id))]
                node_poi_prod = g_poi_type_prod_rate_dict[node_poi_type] * g_poi_id_area_dict[
                    int(float(node.poi_id))] / 1000  # convert the unit of measure to be 1,000 Sq. Ft. GFA
                node.production = node_poi_prod
                g_node_prod_list.append(node_poi_prod)

            # define attraction value of each poi node
            if (int(float(node.poi_id)) in g_poi_id_type_dict.keys()):
                node_poi_type = g_poi_id_type_dict[int(float(node.poi_id))]
                node_poi_attr = g_poi_type_attr_rate_dict[node_poi_type] * g_poi_id_area_dict[
                    int(float(node.poi_id))] / 1000  # convert the unit of measure to be 1,000 Sq. Ft. GFA
                node.attraction = node_poi_attr
                g_node_attr_list.append(node_poi_attr)

        else:
            g_node_prod_list.append(0)
            node.production = 0

            g_node_attr_list.append(0)
            node.attraction = 0
            if (log_flag == 0):
                logger.info("This is not a node producing or attracting demand. Default value of production and "
                            "attraction is 0.")
                log_flag = 1

    # update node.csv with zone_id and demand values
    local_encoding = locale.getdefaultlocale()
    if g_output_folder is not None:
        node_filepath = os.path.join(g_output_folder, 'node.csv')
        try:
            data = pd.read_csv(node_filepath)
        except UnicodeDecodeError:
            data = pd.read_csv(node_filepath, encoding=local_encoding[1])
        data_list = [node.zone_id for node in g_node_list]
        data1 = pd.DataFrame(data_list)
        data['zone_id'] = data1
        data['production'] = pd.DataFrame(g_node_prod_list)
        data['attraction'] = pd.DataFrame(g_node_attr_list)
        data['activity_location_tab'] = pd.DataFrame([node.activity_location_tab for node in g_node_list])
        # print(data)
        data.to_csv(node_filepath, index=False, line_terminator='\n')

    else:
        try:
            data = pd.read_csv('node.csv')
        except UnicodeDecodeError:
            data = pd.read_csv('node.csv', encoding=local_encoding[1])
        data_list = [node.zone_id for node in g_node_list]
        data1 = pd.DataFrame(data_list)
        data['zone_id'] = data1
        data['production'] = pd.DataFrame(g_node_prod_list)
        data['attraction'] = pd.DataFrame(g_node_attr_list)
        # print(data)
        data.to_csv('node.csv', index=False, line_terminator='\n')
    logger.debug('Ending GetNodeDemand')


"""PART 4  CALCULATE ACCESSIBILITY"""
o_zone_id_list = []
o_zone_name_list = []
d_zone_id_list = []
d_zone_name_list = []
od_distance_list = []
od_geometry_list = []
g_distance_matrix = []


def ProduceAccessMatrix(latitude=None, accessibility_folder=None):
    logger.debug('Starting ProduceAccessMatrix')
    global o_zone_id_list
    global o_zone_name_list
    global d_zone_id_list
    global d_zone_name_list
    global od_distance_list
    global od_geometry_list
    global g_distance_matrix
    global g_output_folder
    global g_used_latitude

    g_distance_matrix = np.ones((g_number_of_zones, g_number_of_zones)) * 9999  # initialize distance matrix

    if latitude is None:
        # print('Warning: Latitude is not defined for producing accessibility matrix. Default latitude is 30 degree!')
        logger.warning('Latitude is not defined for producing accessibility matrix! Default latitude is 30 degree.')
        latitude = 30  # comments: default value if no given latitude
        flat_length = g_degree_length_dict[latitude]
        g_used_latitude = latitude

    else:
        # match the closest latitude key according to the given latitude
        dif = float('inf')
        for i in g_degree_length_dict.keys():
            if abs(latitude - i) < dif:
                temp_latitude = i
                dif = abs(latitude - i)
                g_used_latitude = temp_latitude
        flat_length = g_degree_length_dict[temp_latitude]

    print('\nLatitude used for grid2demand = ', g_used_latitude)
    logger.info('Latitude used for grid2demand = ' + str(g_used_latitude))

    # define accessibility by calculating straight distance between zone centroids
    if accessibility_folder:
        accessibility_filepath = os.path.join(accessibility_folder, 'accessibility.csv')
    else:
        accessibility_filepath = 'accessibility.csv'

    o_zone_id_list = []
    o_zone_name_list = []
    d_zone_id_list = []
    d_zone_name_list = []
    od_distance_list = []
    od_geometry_list = []

    for o_zone in g_zone_list:
        for d_zone in g_zone_list:
            o_zone_id_list.append(o_zone.id)
            o_zone_name_list.append(o_zone.name)
            d_zone_id_list.append(d_zone.id)
            d_zone_name_list.append(d_zone.name)
            od_geometry_list.append(
                'LINESTRING (' + str(round(o_zone.centroid_x, 7)) + ' ' + str(round(o_zone.centroid_y, 7))
                + ',' + str(round(d_zone.centroid_x, 7)) + ' ' + str(round(d_zone.centroid_y, 7)) + ')')
            distance_km = (((float(o_zone.centroid_x) - float(d_zone.centroid_x)) * flat_length) ** 2 +
                           ((float(o_zone.centroid_y) - float(d_zone.centroid_y)) * flat_length) ** 2) ** 0.5
            od_distance_list.append(distance_km)
            o_zone_index = g_zone_index_dict[o_zone.id]
            d_zone_index = g_zone_index_dict[d_zone.id]
            g_distance_matrix[o_zone_index][d_zone_index] = distance_km

    # create accessibility.csv
    data = pd.DataFrame(o_zone_id_list)
    print('\nNumber of OD pairs = ', len(o_zone_id_list))
    logger.info('Number of OD pairs = '+str(len(o_zone_id_list)))
    data.columns = ["o_zone_id"]
    data["o_zone_name"] = pd.DataFrame(o_zone_name_list)

    data1 = pd.DataFrame(d_zone_id_list)
    data['d_zone_id'] = data1
    data["d_zone_name"] = pd.DataFrame(d_zone_name_list)

    data2 = pd.DataFrame(od_distance_list)
    data['accessibility'] = data2
    max_accessibility_index = od_distance_list.index(max(od_distance_list))
    sum = 0
    for i in od_distance_list:
        sum += float(i)
    print('\nLargest accessibility of distance = '+str(round(od_distance_list[max_accessibility_index],2))+' km')
    print('Average accessibility of distance = '+str(round(sum/len(od_distance_list),2))+' km')
    logger.info('Largest accessibility of distance = '+str(round(od_distance_list[max_accessibility_index],2))+' km')
    logger.info('Average accessibility of distance = '+str(round(sum/len(od_distance_list),2))+' km')

    data3 = pd.DataFrame(od_geometry_list)
    data['geometry'] = data3

    # print(data)
    if g_output_folder is not None:
        accessibility_filepath = os.path.join(g_output_folder, 'accessibility.csv')
        data.to_csv(accessibility_filepath, index=False, line_terminator='\n')
    else:
        data.to_csv('accessibility.csv', index=False, line_terminator='\n')
    logger.debug("Ending ProduceAccessMatrix")


"""PART 5  TRIP DISTRIBUTION"""
g_node_id_list = []
g_node_zone_id_list = []
g_node_production_dict = {}
g_node_attraction_dict = {}
g_trip_matrix = []
g_total_production_list = []
g_total_attraction_list = []
g_zone_to_nodes_dict = {}


def RunGravityModel(trip_purpose=None, a=None, b=None, c=None):
    logger.debug("Starting RunGravityModel")
    global g_node_id_list
    global g_node_production_dict
    global g_node_attraction_dict
    global g_trip_matrix
    global g_output_folder

    if trip_purpose == None and a == None and b == None and c == None:  # default values of friction factor coefficients for Purpose 1 (HBW)
        a = 28507
        b = -0.02
        c = -0.123

        logger.warning('Trip purpose is not defined! Default trip purpose is Purpose 1.')
        print('\nDefault values of friction factor coefficients under trip purpose 1:', '\na=', a, '\nb=', b,
              '\nc=', c)
        logger.info(
            'Default values of friction factor coefficients under trip purpose 1: \na=' + str(a) + '\nb=' + str(b) +
            '\nc=' + str(c))
    if trip_purpose == 1 and a == None and b == None and c == None:  # default values of friction factor coefficients for Purpose 1
        a = 28507
        b = -0.02
        c = -0.123

        print('\nDefault values of friction factor coefficients under trip purpose 1:', '\na=', a, '\nb=', b,
              '\nc=', c)
        logger.info(
            'Default values of friction factor coefficients under trip purpose 1: \na=' + str(a) + '\nb=' + str(b) +
            '\nc=' + str(c))
    if trip_purpose == 2 and a == None and b == None and c == None:  # default values of friction factor coefficients for Purpose 2
        a = 139173
        b = -1.285
        c = -0.094

        print('\nDefault values of friction factor coefficients under trip purpose 2:', '\na=', a, '\nb=', b,
              '\nc=', c)
        logger.info(
            'Default values of friction factor coefficients under trip purpose 2: \na=' + str(a) + '\nb=' + str(b) +
            '\nc=' + str(c))
    if trip_purpose == 3 and a == None and b == None and c == None:  # default values of friction factor coefficients for Purpose 3
        a = 219113
        b = -1.332
        c = -0.1

        print('\nDefault values of friction factor coefficients under trip purpose 3:', '\na=', a, '\nb=', b,
              '\nc=', c)
        logger.info(
            'Default values of friction factor coefficients under trip purpose 3: \na=' + str(a) + '\nb=' + str(b) +
            '\nc=' + str(c))

    for node in g_node_list:
        g_node_production_dict[node.id] = float(node.production)
        g_node_attraction_dict[node.id] = float(node.attraction)
        g_node_id_list.append(node.id)
        g_node_zone_id_list.append(node.zone_id)
        if node.zone_id != '' and node.zone_id not in g_zone_to_nodes_dict.keys():
            g_zone_to_nodes_dict[node.zone_id] = list()
            g_zone_to_nodes_dict[node.zone_id].append(node.id)
        elif node.zone_id != '':
            g_zone_to_nodes_dict[node.zone_id].append(node.id)

    g_number_of_nodes = len(g_node_list)

    "deal with multiple nodes within one zone"
    g_zone_production = np.zeros(g_number_of_zones)
    g_zone_attraction = np.zeros(g_number_of_zones)
    error_flag = 0
    for i in range(g_number_of_nodes):
        if g_node_list[i].activity_location_tab == 'poi' or g_node_list[i].activity_location_tab == 'boundary' or \
                g_node_list[i].activity_location_tab == 'residential':
            node_id = g_node_id_list[i]
            if g_node_zone_dict.get(node_id) is not None:
                zone_id = g_node_zone_dict[node_id]
                zone_index = g_zone_index_dict[zone_id]
                node_prod = g_node_production_dict[node_id]
                node_attr = g_node_attraction_dict[node_id]
                g_zone_production[zone_index] = g_zone_production[zone_index] + node_prod
                g_zone_attraction[zone_index] = g_zone_attraction[zone_index] + node_attr
                error_flag += 1
    if error_flag == 0:
        # print("There is no node with activity_type = 'poi/residential' or is_boundary = '1'. Please check
        # node.csv!")
        logger.error("There is no node with activity_type = 'poi/residential' or is_boundary = '1'. Please check "
                     "node.csv!")
        sys.exit(0)

    for zone in g_zone_list:
        zone_index = g_zone_index_dict[zone.id]
        g_total_production_list.append(g_zone_production[zone_index])
        g_total_attraction_list.append(g_zone_attraction[zone_index])

    "perform the distribution with friction matrix"
    g_friction_matrix = np.ones((g_number_of_zones, g_number_of_zones)) * 9999  # initialize friction matrix
    for o_zone in g_zone_list:
        for d_zone in g_zone_list:
            o_zone_index = g_zone_index_dict[o_zone.id]
            d_zone_index = g_zone_index_dict[d_zone.id]
            od_distance = g_distance_matrix[o_zone_index][d_zone_index]
            if od_distance != 0:
                g_friction_matrix[o_zone_index][d_zone_index] = a * (od_distance ** b) * (np.exp(c * od_distance))
            else:
                g_friction_matrix[o_zone_index][d_zone_index] = 0

    "step 1: calculate total attraction for each zone"
    g_trip_matrix = np.zeros((g_number_of_zones, g_number_of_zones))
    total_attraction_friction = np.zeros(g_number_of_zones)
    for i in g_zone_id_list:
        prod_zone_index = g_zone_index_dict[i]
        for j in g_zone_id_list:
            attr_zone_index = g_zone_index_dict[j]
            total_attraction_friction[prod_zone_index] += g_zone_attraction[attr_zone_index] * \
                                                          g_friction_matrix[prod_zone_index][attr_zone_index]

    "step 2: update OD matrix"
    for i in g_zone_id_list:
        prod_zone_index = g_zone_index_dict[i]
        for j in g_zone_id_list:
            attr_zone_index = g_zone_index_dict[j]
            g_trip_matrix[prod_zone_index][attr_zone_index] = float(
                g_zone_production[prod_zone_index] * g_zone_attraction[attr_zone_index] *
                g_friction_matrix[prod_zone_index][attr_zone_index] / max(0.000001,
                                                                          total_attraction_friction[prod_zone_index]))


    # create demand.csv
    volume_list = []
    for i in range(len(o_zone_id_list)):
        od_volume = g_trip_matrix[g_zone_index_dict[o_zone_id_list[i]]][g_zone_index_dict[d_zone_id_list[i]]]
        volume_list.append(od_volume)

    data = pd.DataFrame(o_zone_id_list)
    data.columns = ["o_zone_id"]
    data["o_zone_name"] = pd.DataFrame(o_zone_name_list)
    data["d_zone_id"] = pd.DataFrame(d_zone_id_list)
    data["d_zone_name"] = pd.DataFrame(d_zone_name_list)
    data["accessibility"] = pd.DataFrame(od_distance_list)
    data["volume"] = pd.DataFrame(volume_list)
    data["geometry"] = pd.DataFrame(od_geometry_list)

    max_OD_index = volume_list.index(max(volume_list))
    print('\nZone-to-zone OD pair with largest volume is from ' + str(o_zone_name_list[max_OD_index]) + ' to ' +
          str(d_zone_name_list[max_OD_index]))
    logger.info('Zone-to-zone OD pair with largest volume is from ' + str(o_zone_name_list[max_OD_index]) + ' to ' +
          str(d_zone_name_list[max_OD_index]))

    # print(data)
    if g_output_folder is not None:
        demand_filepath = os.path.join(g_output_folder, 'demand.csv')
        data.to_csv(demand_filepath, index=False, line_terminator='\n')
    else:
        data.to_csv('demand.csv', index=False, line_terminator='\n')

    # update zone.csv with total production and attraction in each zone
    data_list = [zone.id for zone in g_zone_list]
    data_zone = pd.DataFrame(data_list)
    data_zone.columns = ["zone_id"]

    data_zone_name_list = [zone.name for zone in g_zone_list]
    data1 = pd.DataFrame(data_zone_name_list)
    data_zone['name'] = data1

    data_list = [zone.centroid_x for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['centroid_x'] = data1

    data_list = [zone.centroid_y for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['centroid_y'] = data1

    data_list = [zone.polygon for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['geometry'] = data1

    data_list = [zone.centroid for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['centroid'] = data1

    data_list = [zone.poi_count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['poi_count'] = data1

    data_zone['total_production'] = pd.DataFrame(g_total_production_list)
    data_zone['total_attraction'] = pd.DataFrame(g_total_attraction_list)

    max_prod_o_zone_index = g_total_production_list.index(max(g_total_production_list))
    max_attr_d_zone_index = g_total_attraction_list.index(max(g_total_attraction_list))
    print('Origin zone with largest production volume is '+str(data_zone_name_list[max_prod_o_zone_index]))
    print('Destination zone with largest attraction volume is ' + str(data_zone_name_list[max_attr_d_zone_index]))
    logger.info('Origin zone with largest production volume is '+str(data_zone_name_list[max_prod_o_zone_index]))
    logger.info('Destination zone with largest attraction volume is ' + str(data_zone_name_list[max_attr_d_zone_index]))

    # print(data_zone)

    if g_output_folder is not None:
        zone_filepath = os.path.join(g_output_folder, 'zone.csv')
        data_zone.to_csv(zone_filepath, index=False, line_terminator='\n')
    else:
        data_zone.to_csv('zone.csv', index=False, line_terminator='\n')
    logger.debug("Ending RunGravityModel")


"""PART 6  GENERATE AGENT"""
agent_list = []


def GenerateAgentBasedDemand():
    logger.debug("Starting GenerateAgentBasedDemand")
    global g_output_folder
    agent_id = 1
    agent_type = 'v'
    if g_output_folder is not None:
        demand_filepath = os.path.join(g_output_folder, 'demand.csv')
        agent_filepath = os.path.join(g_output_folder, 'input_agent.csv')
    else:
        demand_filepath = 'demand.csv'
        agent_filepath = 'input_agent.csv'

    with open(demand_filepath, 'r', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            for i in range(math.ceil(float(line['volume']))):
                agent = Agent(agent_id,
                              agent_type,
                              line['o_zone_id'],
                              line['d_zone_id'])

                # generate o_node_id and d_node_id randomly according to o_zone_id and d_zone_id
                agent.o_node_id = choice(g_zone_to_nodes_dict[str(agent.o_zone_id)])
                agent.d_node_id = choice(g_zone_to_nodes_dict[str(agent.d_zone_id)])
                agent_list.append(agent)
                agent_id += 1
    print('\nNumber of agents = ', len(agent_list))
    logger.info('Number of agents = '+str(len(agent_list)))
    if len(agent_list) == 0:
        print('Empty agent may be caused by empty poi demand. Please check node.csv or poi_trip_rate.csv!')
        logger.warning('Empty agent may be caused by empty poi demand. Please check node.csv or poi_trip_rate.csv!')

    with open(agent_filepath, 'w', newline='', encoding='gbk') as fp:
        writer = csv.writer(fp)
        line = ["agent_id", "agent_type", "o_node_id", "d_node_id", "o_osm_node_id",
                "d_osm_node_id", "o_zone_id", "d_zone_id", "geometry", "departure_time"]
        writer.writerow(line)
        for agent in agent_list:
            from_node = g_node_id_to_node[agent.o_node_id]
            to_node = g_node_id_to_node[agent.d_node_id]
            o_osm_node_id = from_node.osm_node_id
            d_osm_node_id = to_node.osm_node_id
            time_stamp = math.ceil(random.uniform(1, 60))
            if time_stamp == 60:
                departure_time = "0800"
            else:
                if time_stamp < 10:
                    departure_time = "070" + str(time_stamp)
                else:
                    departure_time = "07" + str(time_stamp)
            geometry = "LINESTRING({0} {1},{2} {3})".format(round(from_node.x_coord, 7), round(from_node.y_coord, 7),
                                                            round(to_node.x_coord, 7), round(to_node.y_coord, 7))
            line = [agent.agent_id, agent.agent_type, agent.o_node_id,
                    agent.d_node_id, o_osm_node_id,
                    d_osm_node_id, agent.o_zone_id, agent.d_zone_id, geometry, departure_time]
            writer.writerow(line)
    logger.debug("Ending GenerateAgentBasedDemand")
    # comments:
    # Please visit https://github.com/dabreegster/grid2demand/blob/scenario_script/src/demand_to_abst_scenario.py for simulation in AB Street

