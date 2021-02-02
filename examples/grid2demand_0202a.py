"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Grid2Demand based on osm2gmns
    
    Author: Anjun Li, Southwest Jiaotong University
            Xuesong (Simon) Zhou, Arizona State University
            Entai Wang, Beijing Jiaotong University
            Taehooie Kim, Arizona State University

    Email:  li.anjun@foxmail.com
            xzhou74@asu.ed
            entaiwang@bjtu.edu.cn
            taehooie.kim@asu.edu
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
import pandas as pd
import numpy as np
import math
import csv
import re
import locale
import sys
from pprint import pprint
# from pyproj import Geod
# from shapely import wkt
from collections import defaultdict
import logging
import random
from random import choice


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


class Agent:
    def __init__(self, agent_id, agent_type, o_zone_id,
                 d_zone_id):
        """ the attribute of agent """
        self.agent_id = agent_id
        self.agent_type = agent_type  # vehicle
        self.o_zone_id = int(o_zone_id)
        self.d_zone_id = int(d_zone_id)
        self.o_node_id = 0
        self.d_node_id = 0
        self.path_node_seq_no_list = list()
        self.path_link_seq_no_list = list()
        self.current_link_seq_no_in_path = 0
        self.path_cost = 0
        self.b_generated = False
        self.b_complete_trip = False


# create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

"""PART 1  READ INPUT NETWORK FILES"""
g_node_list = []
g_boundary_node_list = []
g_exclude_boundary_node_list = []
g_poi_list = []
g_poi_id_type_dict = {}
g_poi_id_area_dict = {}
g_exclude_boundary_node_id_index = {}
g_output_folder = ''
g_node_id_to_node = {}


def ReadNetworkFiles(input_folder=None):
    global g_poi_id_type_dict
    global g_poi_id_area_dict
    global g_output_folder

    if input_folder:
        node_filepath = os.path.join(input_folder, 'node.csv')
        poi_filepath = os.path.join(input_folder, 'poi.csv')
        g_output_folder = input_folder
        logfile = os.path.join(g_output_folder, 'log.txt')
    else:
        node_filepath = 'node.csv'
        poi_filepath = 'poi.csv'
        logfile = 'log.txt'

    # create a handler to write the log file
    fh = logging.FileHandler(logfile, mode='w')
    fh.setLevel(logging.DEBUG)

    # create a handler to print out in console
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)

    # define output format
    formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.debug('Starting ReadNetworkFiles')

    with open(node_filepath, errors='ignore') as fp:
        reader = csv.DictReader(fp)
        exclude_boundary_node_index = 0
        for line in reader:
            node = Node()
            node_id = line['node_id']
            if node_id:
                node.id = int(node_id)
            else:
                # print('Error: node_id is not defined in node.csv, please check it!')
                logger.error("node_id is not defined in node.csv, please check it!")
                sys.exit(0)

            osm_node_id = line['osm_node_id']
            if osm_node_id:
                node.osm_node_id = int(float(osm_node_id))
            else:
                node.osm_node_id = None

            x_coord = line['x_coord']
            if x_coord:
                node.x_coord = float(x_coord)
            else:
                # print('Error: x_coord is not defined in node.csv, please check it!')
                logger.error("x_coord is not defined in node.csv, please check it!")
                sys.exit(0)

            y_coord = line['y_coord']
            if y_coord:
                node.y_coord = float(y_coord)
            else:
                # print('Error: y_coord is not defined in node.csv, please check it!')
                logger.error("y_coord is not defined in node.csv, please check it!")
                sys.exit(0)

            poi_id = line['poi_id']
            if poi_id:
                node.poi_id = str(poi_id)
            # else:
            #     logger.error("Please check poi_id in node.csv!")
            #     sys.exit(0)

            boundary_flag = line['is_boundary']
            if boundary_flag:
                node.flag = int(boundary_flag)
            else:
                logger.info("is_boundary is not defined in node.csv. Default value is 0.")
                node.flag = 0

            g_node_id_to_node[node.id] = node
            g_node_list.append(node)

            if node.flag == 1:
                g_boundary_node_list.append(node)
            else:
                g_exclude_boundary_node_list.append(node)
                g_exclude_boundary_node_id_index[node.id] = exclude_boundary_node_index
                exclude_boundary_node_index += 1

    with open(poi_filepath, errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            poi = POI()

            poi_id = line['poi_id']
            if poi_id:
                poi.id = int(poi_id)
            else:
                # print('Error: poi_id is not defined in poi.csv, please check it!')
                logger.error("poi_id is not defined in poi.csv, please check it!")
                sys.exit(0)

            centroid = line['centroid']
            if centroid:
                temp_centroid = str(centroid)
            else:
                # print('Error: centroid is not defined in poi.csv, please check it!')
                logger.error("centroid is not defined in poi.csv, please check it!")
                sys.exit(0)
            str_centroid = temp_centroid.replace('POINT (', '').replace(')', '').replace(' ', ';').strip().split(';')

            x_coord = str_centroid[0]
            if x_coord:
                poi.x_coord = float(x_coord)
            else:
                # print('Error: x_coord is not defined in poi.csv, please check it!')
                logger.error("x_coord is not defined in poi.csv, please check it!")
                sys.exit(0)

            y_coord = str_centroid[1]
            if y_coord:
                poi.y_coord = float(y_coord)
            else:
                # print('Error: y_coord is not defined in poi.csv, please check it!')
                logger.error("y_coord is not defined in poi.csv, please check it!")
                sys.exit(0)

            '''
            # calculate the area of each poi node
            geod = Geod(ellps="WGS84")  # specify a named ellipsoid for calculating poi polygon area
            poi_geometry = str(line['geometry'])
            poly = wkt.loads(poi_geometry)
            area_meter = abs(geod.geometry_area_perimeter(poly)[0])  # calculate poi polygon area in square meters
            '''

            area = line['area']
            if area:
                area_meter = float(area)
            else:
                # print('Error: area is not defined in poi.csv, please check it!')
                logger.error('area is not defined in poi.csv, please check it!')
                sys.exit(0)
            area_feet = area_meter * 10.7639104  # convert the area in square meters to square feet
            poi.area = area_feet

            building = line['building']
            if building:
                poi.type = str(building)
            # else:
            #     # print('Error: building is not defined in poi.csv, please check it!')
            #     logger.error('building is not defined in poi.csv, please check it!')
            #     sys.exit(0)

            g_poi_id_area_dict[poi.id] = poi.area
            g_poi_id_type_dict[poi.id] = poi.type
            g_poi_list.append(poi)

    logger.debug('Ending ReadNetworkFiles')
    # return g_node_list, g_poi_list


"""PART 2  GRID GENERATION"""
g_zone_list = []
g_number_of_zones = 0
g_zone_id_list = []
g_zone_index_dict = {}
g_node_zone_dict = {}
g_poi_zone_dict = {}
g_used_latitude = 0

g_scale_list = [0.006, 0.005, 0.004, 0.003, 0.002, 0.001]
g_degree_length_dict = {60: 55.8, 51: 69.47, 45: 78.85, 30: 96.49,
                        0: 111.3}  # longitudinal length (km) equivalents at selected latitudes

alphabet_list = []
for letter in range(65, 91):
    alphabet_list.append(chr(letter))


def PartitionGrid(number_of_x_blocks=None,
                  number_of_y_blocks=None,
                  cell_width=None,
                  cell_height=None,
                  latitude=None):
    logger.debug('Starting PartitionGrid')

    # Error: Given grid scales and number of blocks simultaneously
    if ((number_of_x_blocks is not None) and (number_of_y_blocks is not None) \
            and (cell_width is not None) and (cell_height is not None)):
        logger.error('Grid scales and number of blocks can only choose ONE to customize!')
        sys.exit(0)

    global g_number_of_zones
    global g_zone_id_list
    global g_zone_index_dict
    global g_node_zone_dict
    global g_used_latitude

    # init parameter
    x_max = max(node.x_coord for node in g_exclude_boundary_node_list)
    x_min = min(node.x_coord for node in g_exclude_boundary_node_list)
    y_max = max(node.y_coord for node in g_exclude_boundary_node_list)
    y_min = min(node.y_coord for node in g_exclude_boundary_node_list)

    if latitude is None:
        latitude = 30  # default value if no given latitude
        flat_length_per_degree_km = g_degree_length_dict[latitude]
        g_used_latitude = latitude
        logger.warning('Latitude is not defined for network partition. Default latitude is 30 degree!')

    else:
        # match the closest latitude key according to the given latitude
        dif = float('inf')
        for i in g_degree_length_dict.keys():
            if abs(latitude - i) < dif:
                temp_latitude = i
                dif = abs(latitude - i)
                g_used_latitude = temp_latitude
        flat_length_per_degree_km = g_degree_length_dict[temp_latitude]

    # Case 0: Default
    if (number_of_x_blocks is None) and (number_of_y_blocks is None) \
            and (cell_width is None) and (cell_height is None):
        logger.warning('Default cell width and height are the length on a flat surface under a specific latitude '
                       'corresponding to the degree of 0.006!')
        scale_x = g_scale_list[0]
        scale_y = g_scale_list[0]
        x_max = math.ceil(x_max / scale_x) * scale_x
        x_min = math.floor(x_min / scale_x) * scale_x
        y_max = math.ceil(y_max / scale_y) * scale_y
        y_min = math.floor(y_min / scale_y) * scale_y
        number_of_x_blocks = round((x_max - x_min) / scale_x)
        number_of_y_blocks = round((y_max - y_min) / scale_y)

    # Case 1: Given number_of_x_blocks and number_of_y_blocks
    if (number_of_x_blocks is not None) and (number_of_y_blocks is not None) \
            and (cell_width is None) and (cell_height is None):
        scale_x = round((x_max - x_min) / number_of_x_blocks, 5) + 0.00001
        scale_y = round((y_max - y_min) / number_of_y_blocks, 5) + 0.00001
        x_max = round(x_min + scale_x * number_of_x_blocks, 5)
        y_min = round(y_max - scale_y * number_of_y_blocks, 5)

    # Case 2: Given scale_x and scale_y in meter
    if (number_of_x_blocks is None) and (number_of_y_blocks is None) \
            and (cell_width is not None) and (cell_height is not None):
        scale_x = round(cell_width / (1000 * flat_length_per_degree_km), 5)
        scale_y = round(cell_height / (1000 * flat_length_per_degree_km), 5)
        x_max = math.ceil(x_max / scale_x) * scale_x
        x_min = math.floor(x_min / scale_x) * scale_x
        y_max = math.ceil(y_max / scale_y) * scale_y
        y_min = math.floor(y_min / scale_y) * scale_y
        number_of_x_blocks = round((x_max - x_min) / scale_x)
        number_of_y_blocks = round((y_max - y_min) / scale_y)

    block_numbers = number_of_x_blocks * number_of_y_blocks
    x_temp = x_min
    y_temp = y_max
    for block_no in range(1, block_numbers + 1):
        block = Zone()
        block.id = block_no
        block.x_min = x_temp
        block.x_max = x_temp + scale_x
        block.y_max = y_temp
        block.y_min = y_temp - scale_y

        for node in g_exclude_boundary_node_list:
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

        # get centroid coordinates of each zone with nodes by calculating average x_coord and y_coord
        if (len(block.node_id_list) != 0):
            block.poi_count = len(block.poi_id_list)
            block.centroid_x = sum(g_exclude_boundary_node_list[g_exclude_boundary_node_id_index[node_id]].x_coord for
                                   node_id in block.node_id_list) / len(block.node_id_list)
            block.centroid_y = sum(g_exclude_boundary_node_list[g_exclude_boundary_node_id_index[node_id]].y_coord for
                                   node_id in block.node_id_list) / len(block.node_id_list)
            str_name_a = str(alphabet_list[math.ceil(block.id / number_of_x_blocks) - 1])
            if int(block.id % number_of_x_blocks) != 0:
                str_name_no = str(int(block.id % number_of_x_blocks))
            else:
                str_name_no = str(number_of_x_blocks)
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

        # centroid of each zone with zero node is the center point of the grid
        if (len(block.node_id_list) == 0):
            block.poi_count = len(block.poi_id_list)
            block.centroid_x = (block.x_max + block.x_min) / 2
            block.centroid_y = (block.y_max + block.y_min) / 2
            str_name_a = str(alphabet_list[math.ceil(block.id / number_of_x_blocks) - 1])
            if int(block.id % number_of_x_blocks) != 0:
                str_name_no = str(int(block.id % number_of_x_blocks))
            else:
                str_name_no = str(number_of_x_blocks)
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

        if round(abs(x_temp + scale_x - x_max) / scale_x) >= 1:
            x_temp = x_temp + scale_x
        else:
            x_temp = x_min
            y_temp = y_temp - scale_y

    # address boundary nodes and generate virtual zones around the boundary of the area

    # left side virtual zones
    i = 1
    delta_y = 0
    while i <= number_of_y_blocks:
        block = Zone()
        block.id = block_numbers + i
        block.name = 'Gate' + str(i)
        block.x_min = x_min - scale_x / 2
        block.x_max = x_min
        block.y_max = y_min + delta_y + scale_y
        block.y_min = y_min + delta_y
        block.centroid_x = block.x_min
        block.centroid_y = (block.y_max + block.y_min) / 2
        block.centroid = 'POINT (' + str(block.centroid_x) + ' ' + str(block.centroid_y) + ')'
        block.polygon = ''
        block.poi_id_list = []
        for node in g_boundary_node_list:
            if abs(node.x_coord - x_min) == min(abs(node.x_coord - x_max), abs(node.x_coord - x_min),
                                                abs(node.y_coord - y_max), abs(node.y_coord - y_min)) \
                    and block.y_max >= node.y_coord >= block.y_min:
                node.zone_id = block.id
                g_node_zone_dict[node.id] = block.id
                block.node_id_list.append(node.id)
        g_zone_list.append(block)
        delta_y += scale_y
        i += 1

    # upper side virtual zones
    i = number_of_y_blocks + 1
    delta_x = 0
    while i <= number_of_y_blocks + number_of_x_blocks:
        block = Zone()
        block.id = block_numbers + i
        block.name = 'Gate' + str(i)
        block.x_min = x_min + delta_x
        block.x_max = x_min + delta_x + scale_x
        block.y_max = y_max + scale_y / 2
        block.y_min = y_max
        block.centroid_x = (block.x_max + block.x_min) / 2
        block.centroid_y = block.y_max
        block.centroid = 'POINT (' + str(block.centroid_x) + ' ' + str(block.centroid_y) + ')'
        block.polygon = ''
        block.poi_id_list = []
        for node in g_boundary_node_list:
            if abs(node.y_coord - y_max) == min(abs(node.x_coord - x_max), abs(node.x_coord - x_min),
                                                abs(node.y_coord - y_max), abs(node.y_coord - y_min)) \
                    and block.x_max >= node.x_coord >= block.x_min:
                node.zone_id = block.id
                g_node_zone_dict[node.id] = block.id
                block.node_id_list.append(node.id)
        g_zone_list.append(block)
        i += 1
        delta_x += scale_x

    # right side virtual zones
    i = number_of_y_blocks + number_of_x_blocks + 1
    delta_y = 0
    while i <= 2 * number_of_y_blocks + number_of_x_blocks:
        block = Zone()
        block.id = block_numbers + i
        block.name = 'Gate' + str(i)
        block.x_min = x_max
        block.x_max = x_max + scale_x / 2
        block.y_max = y_max - delta_y
        block.y_min = y_max - delta_y - scale_y
        block.centroid_x = block.x_max
        block.centroid_y = (block.y_max + block.y_min) / 2
        block.centroid = 'POINT (' + str(block.centroid_x) + ' ' + str(block.centroid_y) + ')'
        block.polygon = ''
        block.poi_id_list = []
        for node in g_boundary_node_list:
            if abs(node.x_coord - x_max) == min(abs(node.x_coord - x_max), abs(node.x_coord - x_min),
                                                abs(node.y_coord - y_max), abs(node.y_coord - y_min)) \
                    and block.y_max >= node.y_coord >= block.y_min:
                node.zone_id = block.id
                g_node_zone_dict[node.id] = block.id
                block.node_id_list.append(node.id)
        g_zone_list.append(block)
        i += 1
        delta_y += scale_y

    # lower side virtual zones
    i = 2 * number_of_y_blocks + number_of_x_blocks + 1
    delta_x = 0
    while i <= 2 * (number_of_y_blocks + number_of_x_blocks):
        block = Zone()
        block.id = block_numbers + i
        block.name = 'Gate' + str(i)
        block.x_min = x_max - delta_x - scale_x
        block.x_max = x_max - delta_x
        block.y_max = y_min
        block.y_min = y_min - scale_y / 2
        block.centroid_x = (block.x_max + block.x_min) / 2
        block.centroid_y = block.y_min
        block.centroid = 'POINT (' + str(block.centroid_x) + ' ' + str(block.centroid_y) + ')'
        block.polygon = ''
        block.poi_id_list = []
        for node in g_boundary_node_list:
            if abs(node.y_coord - y_min) == min(abs(node.x_coord - x_max), abs(node.x_coord - x_min),
                                                abs(node.y_coord - y_max), abs(node.y_coord - y_min)) \
                    and block.x_max >= node.x_coord >= block.x_min:
                node.zone_id = block.id
                g_node_zone_dict[node.id] = block.id
                block.node_id_list.append(node.id)
        g_zone_list.append(block)
        i += 1
        delta_x += scale_x

    g_number_of_zones = len(g_zone_list)
    g_zone_id_list = [zone.id for zone in g_zone_list]
    # get zone index
    for i in range(g_number_of_zones):
        g_zone_index_dict[g_zone_id_list[i]] = i

    # return g_zone_list

    # update poi.csv with zone_id
    local_encoding = locale.getdefaultlocale()
    if g_output_folder is not None:
        poi_filepath = os.path.join(g_output_folder, 'poi.csv')
        try:
            data = pd.read_csv(poi_filepath)
        except UnicodeDecodeError:
            data = pd.read_csv(poi_filepath, encoding=local_encoding[1])
        data_list = [poi.zone_id for poi in g_poi_list]
        data1 = pd.DataFrame(data_list)
        data['zone_id'] = data1
        # print(data)
        data.to_csv(poi_filepath, index=False, line_terminator='\n')

    else:
        try:
            data = pd.read_csv('poi.csv')
        except UnicodeDecodeError:
            data = pd.read_csv('poi.csv', encoding=local_encoding[1])
        data_list = [poi.zone_id for poi in g_poi_list]
        data1 = pd.DataFrame(data_list)
        data['zone_id'] = data1
        # print(data)
        data.to_csv('poi.csv', index=False, line_terminator='\n')

    # create zone.csv
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

    # print(data_zone)
    if g_output_folder is not None:
        zone_filepath = os.path.join(g_output_folder, 'zone.csv')
        data_zone.to_csv(zone_filepath, index=False, line_terminator='\n')
    else:
        data_zone.to_csv('zone.csv', index=False, line_terminator='\n')

    logger.debug("Ending Partition Grid")


"""PART 3  TRIP GENERATION"""
g_trip_purpose = 0
g_poi_type_list = []
g_poi_prod_rate_list = []
g_poi_attr_rate_list = []
g_poi_prod_rate_notes_list = []
g_poi_attr_rate_notes_list = []
g_node_prod_list = []
g_node_attr_list = []
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
        try:
            production_rate = g_poi_purpose_prod_dict[poi_type[i]][trip_purpose]
            g_poi_type_prod_rate_dict[poi_type[i]] = production_rate
            g_poi_prod_rate_flag[poi_type[i]] = 1  # the poi type production rate is obtained from the input table
        except:
            g_poi_type_prod_rate_dict[poi_type[i]] = 0.1  # define default value of production rate
            g_poi_prod_rate_flag[poi_type[i]] = 0  # the poi type production rate does not exist in the input table
            g_number_of_unmatched_poi_production_rate += 1
            logger.info(
                'The POI production rate of ' + "'" + str(poi_type[i]) + "'" +
                ' is NOT defined! Default production rate is 0.1.')
        # define attraction rate of each poi type
        try:
            attraction_rate = g_poi_purpose_attr_dict[poi_type[i]][trip_purpose]
            g_poi_type_attr_rate_dict[poi_type[i]] = attraction_rate
            g_poi_attr_rate_flag[poi_type[i]] = 1  # the poi type attraction rate is obtained from the input table
        except:
            g_poi_type_attr_rate_dict[poi_type[i]] = 0.1  # define default value of attraction rate
            g_poi_attr_rate_flag[poi_type[i]] = 0  # the poi type attraction rate does not exist in the input table
            g_number_of_unmatched_poi_attraction_rate += 1
            logger.info(
                'The POI attraction rate of ' + "'" + str(poi_type[i]) + "'" +
                ' is NOT defined! Default production rate is 0.1.')

    print('\nTrip purpose used for grid2demand is:', g_trip_purpose)
    print('\nTotal number of poi nodes with unmatched production rate are:', g_number_of_unmatched_poi_production_rate)
    print('Total number of poi nodes with unmatched attraction rate are:', g_number_of_unmatched_poi_attraction_rate)
    logger.info('Trip purpose used for grid2demand is: \n' + 'Purpose ' + str(g_trip_purpose))
    logger.info('Total number of poi nodes with unmatched production rate are: \n' + str(
        g_number_of_unmatched_poi_production_rate))
    logger.info('Total number of poi nodes with unmatched attraction rate are: \n' + str(
        g_number_of_unmatched_poi_attraction_rate))

    # create poi_trip_rate.csv
    poi_type = [poi.type for poi in g_poi_list]
    g_poi_type_list = list(set(poi_type))  # obtain unique poi types

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


def GetNodeDemand():
    logger.debug('Starting GetNodeDemand')
    global g_node_prod_list
    global g_node_attr_list
    global g_node_list
    global g_output_folder

    # calculate production/attraction values of each node
    for node in g_node_list:
        if node.flag == 0:  # node is not boundary
            # define production value of each node
            try:
                node_poi_type = g_poi_id_type_dict[int(float(node.poi_id))]
                node_poi_prod = g_poi_type_prod_rate_dict[node_poi_type] * g_poi_id_area_dict[
                    int(float(node.poi_id))] / 1000  # convert the unit of measure to be 1,000 Sq. Ft. GFA
                node.production = node_poi_prod
                g_node_prod_list.append(node_poi_prod)
            except:
                g_node_prod_list.append(0)
                node.production = 0
                logger.info("This is not a poi node. Default value of production is 0.")
            # define attraction value of each node
            try:
                node_poi_type = g_poi_id_type_dict[int(float(node.poi_id))]
                node_poi_attr = g_poi_type_attr_rate_dict[node_poi_type] * g_poi_id_area_dict[
                    int(float(node.poi_id))] / 1000  # convert the unit of measure to be 1,000 Sq. Ft. GFA
                node.attraction = node_poi_attr
                g_node_attr_list.append(node_poi_attr)
            except:
                g_node_attr_list.append(0)
                node.attraction = 0
                logger.info("This is not a poi node. Default value of attraction is 0.")
        else:
            g_node_prod_list.append(1000)  # default production value of boundary node
            node.production = 1000
            g_node_attr_list.append(1000)  # default attraction value of boundary node
            node.attraction = 1000

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
    global d_zone_id_list
    global od_distance_list
    global od_geometry_list
    global g_distance_matrix
    global g_output_folder
    global g_used_latitude

    g_distance_matrix = np.ones((g_number_of_zones, g_number_of_zones)) * 9999  # initialize distance matrix

    if latitude is None:
        # print('Warning: Latitude is not defined for producing accessibility matrix. Default latitude is 30 degree!')
        logger.warning('Latitude is not defined for producing accessibility matrix! Default latitude is 30 degree.')
        latitude = 30  # default value if no given latitude
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

    print('\nLatitude used for grid2demand is:', g_used_latitude)
    logger.info('Latitude used for grid2demand is: \n' + 'Degree ' + str(g_used_latitude))

    # define accessibility by calculating straight distance between zone centroids
    if accessibility_folder:
        accessibility_filepath = os.path.join(accessibility_folder, 'accessibility.csv')
    else:
        accessibility_filepath = 'accessibility.csv'

    # user can define accessibility matrix in advance
    try:
        with open(accessibility_filepath, errors='ignore') as fp:
            reader = csv.DictReader(fp)
            for line in reader:
                o_zone_id = int(line['o_zone_id'])
                o_zone_id_list.append(o_zone_id)
                o_zone_name_list.append(line['o_zone_name'])
                d_zone_id = int(line['d_zone_id'])
                d_zone_id_list.append(d_zone_id)
                d_zone_name_list.append(line['d_zone_name'])
                accessibility = float(line['accessibility'])
                o_zone_index = g_zone_index_dict[o_zone_id]
                d_zone_index = g_zone_index_dict[d_zone_id]
                g_distance_matrix[o_zone_index][d_zone_index] = accessibility
                od_distance_list.append(accessibility)
                od_geometry_list.append(line['geometry'])

    except:
        # print('Warning: Accessibility matrix is not defined. It will be calculated by straight distance between
        # zone centroids ...')
        logger.warning('accessibility.csv does not exist in the current folder. It will be calculated by '
                       'straight-line distance between zone centroids.')
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
    data.columns = ["o_zone_id"]
    data["o_zone_name"] = pd.DataFrame(o_zone_name_list)

    data1 = pd.DataFrame(d_zone_id_list)
    data['d_zone_id'] = data1
    data["d_zone_name"] = pd.DataFrame(d_zone_name_list)

    data2 = pd.DataFrame(od_distance_list)
    data['accessibility'] = data2

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
        # print('Warning: Trip purpose is not defined! Default trip purpose is Purpose 1.')
        # print('Default values of friction factor coefficients are:')
        # print('a=', a)
        # print('b=', b)
        # print('c=', c)
        logger.warning('Trip purpose is not defined! Default trip purpose is Purpose 1.')
        print('\nDefault values of friction factor coefficients under trip purpose 1 are:', '\na=', a, '\nb=', b,
              '\nc=', c)
        logger.info(
            'Default values of friction factor coefficients under trip purpose 1 are: \na=' + str(a) + '\nb=' + str(b) +
            '\nc=' + str(c))
    if trip_purpose == 1 and a == None and b == None and c == None:  # default values of friction factor coefficients for Purpose 1
        a = 28507
        b = -0.02
        c = -0.123
        # print('Default values of friction factor coefficients under trip purpose 1 are:')
        # print('a=', a)
        # print('b=', b)
        # print('c=', c)
        print('\nDefault values of friction factor coefficients under trip purpose 1 are:', '\na=', a, '\nb=', b,
              '\nc=', c)
        logger.info(
            'Default values of friction factor coefficients under trip purpose 1 are: \na=' + str(a) + '\nb=' + str(b) +
            '\nc=' + str(c))
    if trip_purpose == 2 and a == None and b == None and c == None:  # default values of friction factor coefficients for Purpose 2
        a = 139173
        b = -1.285
        c = -0.094
        # print('Default values of friction factor coefficients trip purpose 2 are:')
        # print('a=', a)
        # print('b=', b)
        # print('c=', c)
        print('\nDefault values of friction factor coefficients under trip purpose 2 are:', '\na=', a, '\nb=', b,
              '\nc=', c)
        logger.info(
            'Default values of friction factor coefficients under trip purpose 2 are: \na=' + str(a) + '\nb=' + str(b) +
            '\nc=' + str(c))
    if trip_purpose == 3 and a == None and b == None and c == None:  # default values of friction factor coefficients for Purpose 3
        a = 219113
        b = -1.332
        c = -0.1
        # print('Default values of friction factor coefficients trip purpose 3 are:')
        # print('a=', a)
        # print('b=', b)
        # print('c=', c)
        print('\nDefault values of friction factor coefficients under trip purpose 3 are:', '\na=', a, '\nb=', b,
              '\nc=', c)
        logger.info(
            'Default values of friction factor coefficients under trip purpose 3 are: \na=' + str(a) + '\nb=' + str(b) +
            '\nc=' + str(c))

    for node in g_node_list:
        g_node_production_dict[node.id] = float(node.production)
        g_node_attraction_dict[node.id] = float(node.attraction)
        g_node_id_list.append(node.id)
        g_node_zone_id_list.append(node.zone_id)
        if node.zone_id not in g_zone_to_nodes_dict.keys():
            g_zone_to_nodes_dict[node.zone_id] = list()
            g_zone_to_nodes_dict[node.zone_id].append(node.id)
        else:
            g_zone_to_nodes_dict[node.zone_id].append(node.id)

    g_number_of_nodes = len(g_node_list)

    "deal with multiple nodes within one zone"
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

    for zone in g_zone_list:
        zone_index = g_zone_index_dict[zone.id]
        g_total_production_list.append(g_zone_production[zone_index])
        g_total_attraction_list.append(g_zone_attraction[zone_index])

    "do the distribution with friction matrix"
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

    # model_trip_len = (g_trip_matrix * g_distance_matrix).sum() / g_trip_matrix.sum()
    # print ('final average trip length (model): ', model_trip_len)
    # print('final OD matrix: \n', g_trip_matrix)

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

    data_zone['total_production'] = pd.DataFrame(g_total_production_list)
    data_zone['total_attraction'] = pd.DataFrame(g_total_attraction_list)

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
                agent.o_node_id = choice(g_zone_to_nodes_dict[agent.o_zone_id])
                agent.d_node_id = choice(g_zone_to_nodes_dict[agent.d_zone_id])
                agent_list.append(agent)
                agent_id += 1
    with open(agent_filepath, 'w', newline='', encoding='gbk') as fp:
        writer = csv.writer(fp)
        line = ["agent_id", "agent_type", "o_customized_node_id",
                "d_customized_node_id", "o_osm_node_id",
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
