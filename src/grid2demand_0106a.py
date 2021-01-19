"""
    Grid2Demand based on OSM2GMNS
    Author: Anjun Li, Southwest Jiaotong University
            Xuesong (Simon) Zhou, Arizona State University
            Entai Wang, Beijing Jiaotong University
            Taehooie Kim, Arizona State University

    Email:  li.anjun@foxmail.com
            xzhou74@asu.ed
            entaiwang@bjtu.edu.cn
"""

import os
import pandas as pd
import numpy as np
import math
import csv
import re
import locale
from pprint import pprint
from pyproj import Geod
from shapely import wkt
from collections import defaultdict

class Node:
    def __init__(self):
        self.id = 0
        self.zone_id = 0
        self.x_coord = 0
        self.y_coord = 0
        self.production = 0
        self.attraction = 0
        self.flag = 0  # determine the node is boundary or not
        self.poi_id = ''


class POI:
    def __init__(self):
        self.id = 0
        self.zone_id = 0
        self.x_coord = 0
        self.y_coord = 0
        self.count = 1
        self.area = 0
        self.type = ''


class Zone:
    def __init__(self):
        self.id = 0
        self.name = ''
        self.centroid_x = 0
        self.centroid_y = 0
        self.centroid = ''
        self.x_max = 0
        self.x_min = 0
        self.y_max = 0
        self.y_min = 0
        self.poi_count = 0
        self.node_id_list = []
        self.poi_id_list = []
        self.polygon = ''


"""PART 1  READ INPUT NETWORK FILES"""
g_node_list = []
g_poi_list = []
g_poi_id_type_dict = {}
g_poi_id_area_dict = {}

def readNetworkFile(folder):
    global g_poi_id_type_dict
    global g_poi_id_area_dict

    if folder:
        node_filepath = os.path.join(folder,'node.csv')
        poi_filepath = os.path.join(folder,'poi.csv')
    else:
        node_filepath = 'node.csv'
        poi_filepath = 'poi.csv'

    with open(node_filepath, errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            node = Node()
            node.id = int(line['node_id'])
            node.x_coord = float(line['x_coord'])
            node.y_coord = float(line['y_coord'])
            node.flag = int(line['is_boundary'])
            node.poi_id = str(line['poi_id'])
            g_node_list.append(node)

    with open(poi_filepath, errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            poi = POI()
            poi.id = int(line['poi_id'])
            temp_centroid = str(line['centroid'])
            str_centroid = temp_centroid.replace('POINT (', '').replace(')', '').replace(' ', ';').strip().split(';')
            poi.x_coord = float(str_centroid[0])
            poi.y_coord = float(str_centroid[1])

            # calculate the area of each poi node
            geod = Geod(ellps="WGS84")  # specify a named ellipsoid for calculating poi polygon area
            poi_geometry = str(line['geometry'])
            poly = wkt.loads(poi_geometry)
            area_meter = abs(geod.geometry_area_perimeter(poly)[0])  # calculate poi polygon area in square meters
            area_feet = area_meter * 10.7639104  # convert the area in square meters to square feet
            poi.area = area_feet

            poi.type = str(line['building'])

            g_poi_id_area_dict[poi.id] = poi.area
            g_poi_id_type_dict[poi.id] = poi.type
            g_poi_list.append(poi)

    return g_node_list, g_poi_list


"""PART 2  GRID GENERATION"""
g_zone_list = []
g_number_of_zones = 0
g_zone_id_list = []
g_zone_index_dict = {}
g_node_zone_dict = {}
g_poi_zone_dict = {}

g_scale_list = [0.006, 0.005, 0.004, 0.003, 0.002, 0.001]

alphabet_list = []
for letter in range(65, 91):
    alphabet_list.append(chr(letter))

def NetworkPartition(number_of_x_blocks=None,
                        number_of_y_blocks=None,
                        scale_x=None,
                        scale_y=None):
    global g_number_of_zones
    global g_zone_id_list
    global g_zone_index_dict
    # init parameter
    x_max = max(node.x_coord for node in g_node_list)
    x_min = min(node.x_coord for node in g_node_list)
    y_max = max(node.y_coord for node in g_node_list)
    y_min = min(node.y_coord for node in g_node_list)

    # Case 0: Default
    if (number_of_x_blocks == None) and (number_of_y_blocks == None) \
            and (scale_x == None) and (scale_y == None):
        scale_x = g_scale_list[0]
        scale_y = g_scale_list[0]
        x_max = math.ceil(x_max / scale_x) * scale_x
        x_min = math.floor(x_min / scale_x) * scale_x
        y_max = math.ceil(y_max / scale_y) * scale_y
        y_min = math.floor(y_min / scale_y) * scale_y
        number_of_x_blocks = round((x_max - x_min) / scale_x)
        number_of_y_blocks = round((y_max - y_min) / scale_y)

    # Case 1: Given number_of_x_blocks and number_of_y_blocks
    if (number_of_x_blocks != None) and (number_of_y_blocks != None) \
            and (scale_x == None) and (scale_y == None):
        scale_x = (x_max - x_min) / number_of_x_blocks
        scale_y = (y_max - y_min) / number_of_y_blocks

        # Case 2: Given scale_x and scale_y
    if (number_of_x_blocks == None) and (number_of_y_blocks == None) \
            and (scale_x != None) and (scale_y != None):
        x_max = math.ceil(x_max / scale_x) * scale_x
        x_min = math.floor(x_min / scale_x) * scale_x
        y_max = math.ceil(y_max / scale_y) * scale_y
        y_min = math.floor(y_min / scale_y) * scale_y
        number_of_x_blocks = round((x_max - x_min) / scale_x)
        number_of_y_blocks = round((y_max - y_min) / scale_y)

    block_numbers = number_of_x_blocks * number_of_y_blocks

    x_temp = x_min
    y_temp = y_min
    for block_no in range(0, block_numbers):
        block = Zone()
        block.id = block_no
        block.x_min = x_temp
        block.x_max = x_temp + scale_x
        block.y_min = y_temp
        block.y_max = y_temp + scale_y

        for node in g_node_list:
            if ((node.x_coord <= block.x_max) & (node.x_coord >= block.x_min) \
                    & (node.y_coord <= block.y_max) & (node.y_coord >= block.y_min)):
                node.zone_id = block.id
                g_node_zone_dict[node.id] = block.id
                block.node_id_list.append(node.id)

        for poi in g_poi_list:
            if ((poi.x_coord <= block.x_max) & (poi.x_coord >= block.x_min) \
                    & (poi.y_coord <= block.y_max) & (poi.y_coord >= block.y_min)):
                poi.zone_id = block.id
                g_poi_zone_dict[poi.id] = block.id
                block.poi_id_list.append(poi.id)
        if (len(block.node_id_list) != 0):
            block.poi_count = sum(g_poi_list[poi_id].count for poi_id in block.poi_id_list)
            block.centroid_x = sum(g_node_list[node_id].x_coord for node_id in block.node_id_list) / len(
                block.node_id_list)
            block.centroid_y = sum(g_node_list[node_id].y_coord for node_id in block.node_id_list) / len(
                block.node_id_list)
            str_name_a = str(alphabet_list[round(block.id / number_of_x_blocks)])
            str_name_no = str(int(block.id % number_of_x_blocks))
            block.name = str_name_a + str_name_no

            str_polygon = 'POLYGON ((' + \
                          str(block.x_min) + ' ' + str(block.y_min) + ',' + \
                          str(block.x_min) + ' ' + str(block.y_max) + ',' + \
                          str(block.x_max) + ' ' + str(block.y_max) + ',' + \
                          str(block.x_max) + ' ' + str(block.y_min) + ',' + \
                          str(block.x_min) + ' ' + str(block.y_min) + '))'
            block.polygon = str_polygon

            str_centroid = 'POINT (' + str(block.centroid_x) + ' ' + str(block.centroid_y) + ')'
            block.centroid = str_centroid
            g_zone_list.append(block)

        if (x_temp + scale_x < x_max):
            x_temp = x_temp + scale_x
        else:
            x_temp = x_min
            y_temp = y_temp + scale_y

    g_number_of_zones = len(g_zone_list)
    g_zone_id_list = [zone.id for zone in g_zone_list]
    # get zone index
    for i in range(g_number_of_zones):
        g_zone_index_dict[g_zone_id_list[i]] = i

    return g_zone_list


"""PART 3  TRIP GENERATION"""
g_trip_purpose = []
g_poi_type_list = []
g_poi_prod_rate_list = []
g_poi_attr_rate_list = []
g_node_prod_list = []
g_node_attr_list = []
g_external_trip_purpose = ['HBW', 'NHB', 'HBO']
g_poi_type_prod_rate_dict = {}
g_poi_type_attr_rate_dict = {}
g_poi_purpose_prod_dict = defaultdict(defaultdict)
g_poi_purpose_attr_dict = defaultdict(defaultdict)

def getPoiTripRate(trip_rate_folder = None,
                   trip_purpose = None):
    global g_poi_purpose_prod_dict
    global g_poi_purpose_attr_dict
    global g_poi_type_list
    global g_poi_type_prod_rate_dict
    global g_poi_type_attr_rate_dict
    global g_trip_purpose

    # define production/attraction rates of each land use type and trip purpose
    if trip_rate_folder is None:
        # default trip generation rates refer to ITE Trip Generation Manual, 10t Edition
        # https://www.troutdaleoregon.gov/sites/default/files/fileattachments/public_works/page/966/ite_land_use_list_10th_edition.pdf
        # unit of measure for all poi nodes is 1,000 SF GFA in this version
        g_poi_purpose_prod_dict = {'library': {'HBW': 8.16}, 'university': {'HBW': 1.17}, 'office': {'HBW': 2.04}, \
                                   'arts_centre': {'HBW': 0.18}, 'university;yes': {'HBW': 1.17},
                                   'bank': {'HBW': 12.13}, \
                                   'childcare': {'HBW': 11.12}, 'school': {'HBW': 2.04}, 'public': {'HBW': 4.79}, \
                                   'post_office': {'HBW': 11.21}, 'pharmacy': {'HBW': 10.29}, 'yes': {'HBW': 1.15}}
        # users can customize production rates of each poi type with a specific trip purpose
        g_poi_purpose_attr_dict = {'parking': {'HBW': 2.39}, 'apartments': {'HBW': 0.48},
                                   'motorcycle_parking': {'HBW': 2.39}, \
                                   'theatre': {'HBW': 6.17}, 'restaurant': {'HBW': 7.80}, 'cafe': {'HBW': 36.31}, \
                                   'bar': {'HBW': 7.80}, 'bicycle_parking': {'HBW': 2.39}, 'residential': {'HBW': 0.48}, \
                                   'commercial': {'HBW': 3.81}, 'house': {'HBW': 0.48}, 'stadium': {'HBW': 0.47}, \
                                   'retail': {'HBW': 6.84}, 'fast_food': {'HBW': 14.13}, 'yes': {'HBW': 1.15}}
    else:
        # user can customize poi_trip_rate.csv in advance
        filepath = os.path.join(trip_rate_folder, 'poi_trip_rate.csv')
        with open(filepath, errors='ignore') as fp:
            reader = csv.DictReader(fp)
            for line in reader:
                poi_type = line['building']
                trip_purpose = line['trip_purpose']
                g_poi_purpose_prod_dict[poi_type][trip_purpose] = float(line['production_rate'])
                g_poi_purpose_attr_dict[poi_type][trip_purpose] = float(line['attraction_rate'])

    # Get POI production/attraction rates of each poi type with a specific trip purpose
    if trip_purpose is None:
        trip_purpose = g_external_trip_purpose[0]  # default trip purpose is Home-based Work
        g_trip_purpose.append(trip_purpose)
    else:
        trip_purpose = trip_purpose
        g_trip_purpose.append(trip_purpose)

    poi_id = [poi.id for poi in g_poi_list]
    poi_type = [poi.type for poi in g_poi_list]
    for i in range(len(poi_id)):
        # define production rate of each poi type
        try:
            production_rate = g_poi_purpose_prod_dict[poi_type[i]][trip_purpose]
            g_poi_type_prod_rate_dict[poi_type[i]] = production_rate
        except:
            g_poi_type_prod_rate_dict[poi_type[i]] = 0.1  # define default value of production rate
        # define attraction rate of each poi type
        try:
            attraction_rate = g_poi_purpose_attr_dict[poi_type[i]][trip_purpose]
            g_poi_type_attr_rate_dict[poi_type[i]] = attraction_rate
        except:
            g_poi_type_attr_rate_dict[poi_type[i]] = 0.1  # define default value of attraction rate


def getNodeDemand():
    global g_node_prod_list
    global g_node_attr_list
    global g_node_list

    # calculate production/attraction values of each node
    for node in g_node_list:
        if node.flag == 0:  # node is not boundary
            # define production value of each node
            try:
                node_poi_type = g_poi_id_type_dict[int(float(node.poi_id))]
                node_poi_prod = g_poi_type_prod_rate_dict[node_poi_type] * g_poi_id_area_dict[
                    int(float(node.poi_id))] / 1000
                node.production = node_poi_prod
                g_node_prod_list.append(node_poi_prod)
            except:
                g_node_prod_list.append(0)
                node.production = 0
            # define attraction value of each node
            try:
                node_poi_type = g_poi_id_type_dict[int(float(node.poi_id))]
                node_poi_attr = g_poi_type_attr_rate_dict[node_poi_type] * g_poi_id_area_dict[
                    int(float(node.poi_id))] / 1000
                node.attraction = node_poi_attr
                g_node_attr_list.append(node_poi_attr)
            except:
                g_node_attr_list.append(0)
                node.attraction = 0

        else:  # node is a boundary
            g_node_prod_list.append(1000)  # default production value of boundary node
            node.production = 1000
            g_node_attr_list.append(1000)  # default attraction value of boundary node
            node.attraction = 1000


"""PART 4  CALCULATE ACCESSIBILITY"""
o_zone_id_list = []
d_zone_id_list = []
od_distance_list = []
od_geometry_list = []
g_degree_length_dict = {60:55.8, 51:69.47, 45:78.85, 30:96.49, 0:111.3}  # longitudinal length (km) equivalents at selected latitudes
g_distance_matrix = []

def AccessMatrix(latitude = None):
    global o_zone_id_list
    global d_zone_id_list
    global od_distance_list
    global od_geometry_list
    global g_distance_matrix

    g_distance_matrix = np.ones((g_number_of_zones, g_number_of_zones)) * 9999  # initialize distance matrix

    if latitude is None:
        latitude = 30  # default value if no given latitude
        flat_length = g_degree_length_dict[latitude]

    else:
        # match the closest latitude key according to the given latitude
        dif = float('inf')
        for i in g_degree_length_dict.keys():
            if abs(latitude - i) < dif:
                temp_latitude = i
                dif = abs(latitude - i)
        flat_length = g_degree_length_dict[temp_latitude]


    for o_zone in g_zone_list:
        for d_zone in g_zone_list:
            o_zone_id_list.append(o_zone.id)
            d_zone_id_list.append(d_zone.id)
            od_geometry_list.append('LINESTRING ('+str(o_zone.centroid_x)+' '+str(o_zone.centroid_y)+','+\
                               str(d_zone.centroid_x)+' '+str(d_zone.centroid_y)+')')
            distance_km = (((float(o_zone.centroid_x) - float(d_zone.centroid_x)) * flat_length) ** 2 + \
                          ((float(o_zone.centroid_y) - float(d_zone.centroid_y)) * flat_length) ** 2) ** 0.5
            od_distance_list.append(distance_km)
            o_zone_index = g_zone_index_dict[o_zone.id]
            d_zone_index = g_zone_index_dict[d_zone.id]
            g_distance_matrix[o_zone_index][d_zone_index] = distance_km


"""PART 5  TRIP DISTRIBUTION"""
g_node_id_list = []
g_node_production_dict = {}
g_node_attraction_dict = {}
g_node_zone_dict = {}
g_trip_matrix = []

def GravityModel():
    global g_node_id_list
    global g_node_production_dict
    global g_node_attraction_dict
    global g_node_zone_dict
    global g_trip_matrix

    for node in g_node_list:
        g_node_production_dict[node.id] = int(float(node.production))
        g_node_attraction_dict[node.id] = int(float(node.attraction))
        g_node_zone_dict[node.id] = node.zone_id

    g_node_id_list = [node.id for node in g_node_list]
    g_number_of_nodes = len(g_node_list)

    "deal with multiple nodes with a single zone"
    g_zone_production = np.zeros(g_number_of_zones)
    g_zone_attraction = np.zeros(g_number_of_zones)
    for i in range(g_number_of_nodes):
        node_id = g_node_id_list[i]
        zone_id = g_node_zone_dict[node_id]
        zone_index = g_zone_index_dict[zone_id]
        node_prod = g_node_production_dict[node_id]
        node_attr = g_node_attraction_dict[node_id]
        g_zone_production[zone_index] = g_zone_production[zone_index] + node_prod
        g_zone_attraction[zone_index] = g_zone_attraction[zone_index] + node_attr

    "do the distribution with friction matrix"
    beta = -0.1
    g_friction_matrix = np.exp(beta * g_distance_matrix)
    # print(friction_matrix)

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

    #model_trip_len = (g_trip_matrix * g_distance_matrix).sum() / g_trip_matrix.sum()
    # print ('final average trip length (model): ', model_trip_len)
    # print('final OD matrix: \n', g_trip_matrix)


"""PART 6  OUTPUT FILES"""
def outputCSV(output_folder):
    # DataFrame framework
    node_filepath = os.path.join(output_folder, 'node.csv')
    poi_filepath = os.path.join(output_folder, 'poi.csv')
    zone_filepath = os.path.join(output_folder, 'zone.csv')
    triprate_filepath = os.path.join(output_folder, 'poi_trip_rate.csv')
    accessibility_filepath = os.path.join(output_folder, 'accessibility.csv')
    demand_filepath = os.path.join(output_folder, 'demand.csv')

    # 1. update node.csv with zone_id
    local_encoding = locale.getdefaultlocale()
    try:
        data = pd.read_csv(node_filepath)
    except UnicodeDecodeError:
        data = pd.read_csv(node_filepath, encoding=local_encoding[1])
    data_list = [node.zone_id for node in g_node_list]
    data1 = pd.DataFrame(data_list)
    data['zone_id'] = data1
    data['production'] = pd.DataFrame(g_node_prod_list)
    data['attraction'] = pd.DataFrame(g_node_attr_list)
    #print(data)
    data.to_csv(node_filepath,index =False)

    # 2. update poi.csv with zone_id
    try:
        data = pd.read_csv(poi_filepath)
    except UnicodeDecodeError:
        data = pd.read_csv(poi_filepath, encoding=local_encoding[1])
    data_list = [poi.zone_id for poi in g_poi_list]
    data1 = pd.DataFrame(data_list)
    data['zone_id'] = data1
    #print(data)
    data.to_csv(poi_filepath,index =False)

    # 3. generate zone.csv
    data_list = [zone.id for zone in g_zone_list]
    data_zone = pd.DataFrame(data_list)
    data_zone.columns = ["zone_id"]

    data_list = [zone.name for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
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

    #print(data_zone)
    data_zone.to_csv(zone_filepath, index=False)

    # 4. generate poi_trip_rate.csv
    poi_type = [poi.type for poi in g_poi_list]
    g_poi_type_list = list(set(poi_type))  # obtain unique poi types

    data_index = [i for i in range(len(g_poi_type_list))]
    data_rate = pd.DataFrame(data_index)
    data_rate.columns = ["poi_type_id"]

    data_type = [building for building in g_poi_type_list]
    data_rate['building'] = pd.DataFrame(data_type)

    data_rate['unit_of_measure'] = pd.DataFrame(['1,000 Sq. Ft. GFA']*len(g_poi_type_list))

    data_rate['trip_purpose'] = pd.DataFrame([g_trip_purpose]*len(g_poi_type_list))

    for item in g_poi_type_list:
        g_poi_prod_rate_list.append(g_poi_type_prod_rate_dict[item])
        g_poi_attr_rate_list.append(g_poi_type_attr_rate_dict[item])

    data_rate['production_rate'] = pd.DataFrame(g_poi_prod_rate_list)

    data_rate['attraction_rate'] = pd.DataFrame(g_poi_attr_rate_list)

    #print(data_rate)
    data_rate.to_csv(triprate_filepath,index=False)

    # 5. generate accessibility.csv
    data = pd.DataFrame(o_zone_id_list)
    data.columns = ["o_zone_id"]
    data1 = pd.DataFrame(d_zone_id_list)
    data['d_zone_id'] = data1

    data2 = pd.DataFrame(od_distance_list)
    data['accessibility (km)'] = data2

    data3 = pd.DataFrame(od_geometry_list)
    data['geometry'] = data3

    #print(data)
    data.to_csv(accessibility_filepath,index =False)

    # 6. generate demand.csv
    volume_list = []
    for i in range(len(o_zone_id_list)):
        od_volume = g_trip_matrix[o_zone_id_list[i]][d_zone_id_list[i]]
        volume_list.append(od_volume)

    data = pd.DataFrame(o_zone_id_list)
    data.columns = ["o_zone_id"]

    data["d_zone_id"] = pd.DataFrame(d_zone_id_list)
    data["accessibility"] = pd.DataFrame(od_distance_list)
    data["volume"] = pd.DataFrame(volume_list)
    data["geometry"] = pd.DataFrame(od_geometry_list)

    #print(data)
    data.to_csv(demand_filepath, index=False)