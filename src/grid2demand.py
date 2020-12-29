"""
    Grid2Demand based on OSM2GMNS
"""

import osm2gmns as og
import os
import pandas as pd
import numpy as np
import math
import csv
import re
from pprint import pprint

"""PART 1  GRID GENERATION"""

g_scale_list = [0.006, 0.005, 0.004, 0.003, 0.002, 0.001]
scale_x = g_scale_list[0]
scale_y = g_scale_list[0]

alphabet_list = []
for letter in range(65,91):
    alphabet_list.append(chr(letter))

class Node:
    def __init__(self):
        self.id = 0
        self.zone_id = 0
        self.x_coord = 0
        self.y_coord = 0


class POI:
    def __init__(self):
        self.id = 0
        self.zone_id = 0
        self.x_coord = 0
        self.y_coord = 0
        self.value = 1


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
        self.count = 0
        self.node_id_list = []
        self.poi_id_list = []
        self.polygon = ''


g_node_list = []
g_poi_list = []
g_zone_list = []
g_node_zone_dict = {}
g_poi_zone_dict = {}
#g_poi_demand_dict = {}


def g_ReadInputData():
    with open(r'node.csv', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            node = Node()
            node.id = int(line['node_id'])
            node.x_coord = float(line['x_coord'])
            node.y_coord = float(line['y_coord'])
            g_node_list.append(node)

    with open(r'poi.csv', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            poi = POI()
            poi.id = int(line['poi_id'])
            temp_centroid = str(line['centroid'])
            str_centroid = temp_centroid.replace('POINT (', '').replace(')', '').replace(' ', ';').strip().split(';')
            poi.x_coord = float(str_centroid[0])
            poi.y_coord = float(str_centroid[1])

            g_poi_list.append(poi)


def g_network_partition():
    # init parameter
    global number_of_x_blocks
    global number_of_y_blocks

    x_max = max(node.x_coord for node in g_node_list)
    x_min = min(node.x_coord for node in g_node_list)
    y_max = max(node.y_coord for node in g_node_list)
    y_min = min(node.y_coord for node in g_node_list)

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
            block.count = sum(g_poi_list[poi_id].value for poi_id in block.poi_id_list)
            block.centroid_x = sum(g_node_list[node_id].x_coord for node_id in block.node_id_list) / len(
                block.node_id_list)
            block.centroid_y = sum(g_node_list[node_id].y_coord for node_id in block.node_id_list) / len(
                block.node_id_list)
            str_name_a = str(alphabet_list[round(block.id / number_of_x_blocks)])
            str_name_no = str(int(block.id % number_of_x_blocks))
            block.name = str_name_a + str_name_no

            str_polygon = 'POLYGON ((' + \
                str(block.x_min) + ' ' +str(block.y_min) + ',' + \
                str(block.x_min) + ' ' +str(block.y_max) + ',' + \
                str(block.x_max) + ' ' +str(block.y_max) + ',' + \
                str(block.x_max) + ' ' +str(block.y_min) + ',' + \
                str(block.x_min) + ' ' +str(block.y_min) + '))'
            block.polygon = str_polygon

            str_centroid = 'POINT (' + str(block.centroid_x) + ' ' + str(block.centroid_y) + ')'
            block.centroid = str_centroid
            g_zone_list.append(block)

        if (x_temp + scale_x < x_max):
            x_temp = x_temp + scale_x
        else:
            x_temp = x_min
            y_temp = y_temp + scale_y
    

def g_output_zone():
    # DataFrame framework
    # update node.csv with zone_id
    data = pd.read_csv(r"node.csv",encoding='utf-8')
    data_list = [node.zone_id for node in g_node_list]
    data1 = pd.DataFrame(data_list)
    data['zone_id'] = data1
    print(data)
    data.to_csv(r"node.csv",index =False)

    # update poi.csv with zone_id
    data = pd.read_csv(r"poi.csv",encoding='utf-8')
    data_list = [poi.zone_id for poi in g_poi_list]
    data1 = pd.DataFrame(data_list)
    data['zone_id'] = data1
    print(data)
    data.to_csv(r"poi.csv",index =False)

    # generate zone.csv
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

    data_list = [zone.count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['poi_count'] = data1


    print(data_zone)
    data_zone.to_csv(r"zone.csv",index =False)


"""PART 2  TRIP GENERATION"""

g_poi_type_list = []
g_poi_prod_list = []
g_poi_attr_list = []
g_node_prod_list = []
g_node_attr_list = []
g_external_trip_purpose = ['HBW', 'NHB', 'HBO']
g_poi_type_prod_dict = {}
g_poi_type_attr_dict = {}
g_poi_id_type_dict = {}
g_poi_purpose_prod_dict = {'parking':{'HBW':400},'apartments':{'HBW':300}}
# users can customize production rates of each poi type with a specific trip purpose
g_poi_purpose_attr_dict = {'library':{'HBW':500},'university':{'HBW':20}}
# users can customize attraction rates of each poi type with a specific trip purpose

def g_poi_demand():
    global g_poi_type_list

    with open(r'poi.csv', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            poi_type = line['building']
            g_poi_type_list.append(poi_type)
            trip_purpose = g_external_trip_purpose[0]  # default trip purpose is Home-based Work
            try:
                production_rate = g_poi_purpose_prod_dict[poi_type][trip_purpose]
                g_poi_type_prod_dict[poi_type] = production_rate
            except:
                g_poi_type_prod_dict[poi_type] = 10  # define default value of production

            try:
                attraction_rate = g_poi_purpose_attr_dict[poi_type][trip_purpose]
                g_poi_type_attr_dict[poi_type] = attraction_rate
            except:
                g_poi_type_attr_dict[poi_type] = 10  # define default value of attraction

    g_poi_type_list = list(set(g_poi_type_list))  # obtain unique poi types

    # output poi_trip_rate.csv
    data_index = [i for i in range(len(g_poi_type_list))]
    data_poi = pd.DataFrame(data_index)
    data_poi.columns = ["poi_type_id"]

    data_type = [building for building in g_poi_type_list]
    data_poi['building'] = pd.DataFrame(data_type)

    data_poi['trip_purpose'] = pd.DataFrame([trip_purpose]*len(g_poi_type_list))

    for item in g_poi_type_list:
        g_poi_prod_list.append(g_poi_type_prod_dict[item])
        g_poi_attr_list.append(g_poi_type_attr_dict[item])

    data_poi['production'] = pd.DataFrame(g_poi_prod_list)

    data_poi['attraction'] = pd.DataFrame(g_poi_attr_list)

    data_poi.to_csv(r"poi_trip_rate.csv",index=False)

def g_node_demand():
    global g_poi_type_prod_dict
    global g_poi_type_attr_dict
    with open(r'poi.csv', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            g_poi_id_type_dict[int(line['poi_id'])] = line['building']

    # user can customize poi_trip_rate.csv in advance
    '''
    with open(r'poi_trip_rate.csv', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            poi_type = line['building']
            trip_purpose = line['trip_purpose']
            g_poi_purpose_prod_dict[poi_type][trip_purpose] = line['production']
            g_poi_purpose_attr_dict[poi_type][trip_purpose] = line['attraction']
    '''

    # update node.csv
    node_file = pd.read_csv(r'node.csv')
    for line in node_file.values:
        node_poi_id = line[12]
        node_zone_id = line[4]
        if line[8] == 0:  # node is not boundary
            try:
                node_poi_type = g_poi_id_type_dict[int(node_poi_id)]
                node_poi_prod = g_poi_type_prod_dict[node_poi_type]
            except:
                node_poi_prod = 0

            try:
                node_poi_type = g_poi_id_type_dict[int(node_poi_id)]
                node_poi_attr = g_poi_type_attr_dict[node_poi_type]
            except:
                node_poi_attr = 0
        else:
            node_poi_prod = 1000  # default production value of boundary node
            node_poi_attr = 1000  # default attraction value of boundary node

        g_node_prod_list.append(node_poi_prod)
        g_node_attr_list.append(node_poi_attr)

    node_file['production'] = pd.DataFrame(g_node_prod_list)
    node_file['attraction'] = pd.DataFrame(g_node_attr_list)

    node_file.to_csv(r'node.csv', index=False)


"""PART 3  CALCULATE ACCESSIBILITY"""

g_zone_list = []
g_degree_length_dict = {60:55.8, 51:69.47, 45:78.85, 30:96.49, 0:111.3}
# longitudinal length equivalents at selected latitudes
given_latitude = 30  # default value; user can customize it

# match the closest latitude key according to the given latitude
dif = float('inf')
for i in g_degree_length_dict.keys():
    if abs(given_latitude - i) < dif:
        latitude = i
        dif = abs(given_latitude - i)

flat_length = g_degree_length_dict[latitude]

def g_access_mtrx():
    with open(r'zone.csv') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            zone = Zone()
            zone.id = int(line['zone_id'])
            zone.centroid_x = float(line['centroid_x'])
            zone.centroid_y = float(line['centroid_y'])

            g_zone_list.append(zone)

    o_zone_id_list = []
    d_zone_id_list = []
    od_distance = []
    od_geometry = []
    for o_zone in g_zone_list:
        for d_zone in g_zone_list:
            o_zone_id_list.append(o_zone.id)
            d_zone_id_list.append(d_zone.id)
            od_geometry.append('LINESTRING ('+str(o_zone.centroid_x)+' '+str(o_zone.centroid_y)+','+\
                               str(d_zone.centroid_x)+' '+str(d_zone.centroid_y)+')')
            od_distance.append((((float(o_zone.centroid_x) - float(d_zone.centroid_x)) * flat_length) ** 2 + \
                          ((float(o_zone.centroid_y) - float(d_zone.centroid_y)) * flat_length)**2) ** 0.5)

    # output access_matrix.csv
    data = pd.DataFrame(o_zone_id_list)
    data.columns = ["o_zone_id"]
    data1 = pd.DataFrame(d_zone_id_list)
    data['d_zone_id'] = data1

    data2 = pd.DataFrame(od_distance)
    data['accessibility'] = data2

    data3 = pd.DataFrame(od_geometry)
    data['geometry'] = data3


    print(data)
    data.to_csv(r"accessibility.csv",index =False)


"""PART 4  TRIP DISTRIBUTION"""

def gravity_model():
    "read node.csv to get the inforamtion of nodes, zones"
    g_node_list = []
    g_zone_list = []

    g_node_production_dict = {}
    g_node_attraction_dict = {}
    g_node_zone_dict = {}

    with open(r'node.csv', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            zone = line['zone_id']
            g_zone_list.append(zone)

            node = line['node_id']
            g_node_list.append(node)

            production = line['production']
            try:
                g_node_production_dict[node] = int(production)
            except:
                g_node_production_dict[node] = 0

            attraction = line['attraction']
            try:
                g_node_attraction_dict[node] = int(attraction)
            except:
                g_node_attraction_dict[node] = 0

            g_node_zone_dict[node] = zone

    g_zone_list = list(set(g_zone_list))  # get zone list with unique zone id
    g_number_of_zones = len(g_zone_list)
    g_number_of_nodes = len(g_node_list)

    "get zone index"
    g_zone_index_dict = {}
    for i in range(g_number_of_zones):
        g_zone_index_dict[g_zone_list[i]] = i
    # print(g_zone_index_dict)

    "deal with multiple nodes with a single zone"
    g_zone_production = np.zeros(g_number_of_zones)
    g_zone_attraction = np.zeros(g_number_of_zones)
    for i in range(g_number_of_nodes):
        node = g_node_list[i]
        zone = g_node_zone_dict[node]
        zone_index = g_zone_index_dict[zone]
        node_prod = g_node_production_dict[node]
        node_attr = g_node_attraction_dict[node]
        g_zone_production[zone_index] = g_zone_production[zone_index] + node_prod
        g_zone_attraction[zone_index] = g_zone_attraction[zone_index] + node_attr
    # print(g_zone_production)

    "initialize distance matrix"
    g_distance_matrix = np.ones((g_number_of_zones, g_number_of_zones)) * 9999

    "read agent.csv to update distance matrix"
    with open(r'accessibility.csv', errors='ignore') as fd:
        reader = csv.DictReader(fd)
        for line in reader:
            o_zone_index = g_zone_index_dict[line['o_zone_id']]
            d_zone_index = g_zone_index_dict[line['d_zone_id']]
            g_distance_matrix[o_zone_index][d_zone_index] = float(line['accessibility'])
    # print(distance_matrix)

    "do the distribution with friction matrix"
    beta = -0.1
    g_trip_matrix = np.zeros((g_number_of_zones, g_number_of_zones))
    g_friction_matrix = np.exp(beta * g_distance_matrix)
    # print(friction_matrix)

    "step 1: calculate total attraction for each zone"
    total_attraction_friction = np.zeros(g_number_of_zones)
    for i in g_zone_list:
        prod_zone_index = g_zone_index_dict[i]
        for j in g_zone_list:
            attr_zone_index = g_zone_index_dict[j]
            total_attraction_friction[prod_zone_index] += g_zone_attraction[attr_zone_index] * \
                                                          g_friction_matrix[prod_zone_index][attr_zone_index]

    "step 2: update OD matrix"
    for i in g_zone_list:
        prod_zone_index = g_zone_index_dict[i]
        for j in g_zone_list:
            attr_zone_index = g_zone_index_dict[j]
            g_trip_matrix[prod_zone_index][attr_zone_index] = float(
                g_zone_production[prod_zone_index] * g_zone_attraction[attr_zone_index] *
                g_friction_matrix[prod_zone_index][attr_zone_index] / max(0.000001,
                                                                          total_attraction_friction[prod_zone_index]))

    model_trip_len = (g_trip_matrix * g_distance_matrix).sum() / g_trip_matrix.sum()

    # print ('final average trip length (model): ', model_trip_len)
    # print('final OD matrix: \n', g_trip_matrix)

    # output demand.csv
    volume_list = []
    o_zone_id_list = []
    d_zone_id_list = []
    geometry_list = []
    accessibility_list = []
    with open(r'accessibility.csv', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            o_zone = g_zone_index_dict[str(line['o_zone_id'])]
            d_zone = g_zone_index_dict[str(line['d_zone_id'])]
            od_volume = g_trip_matrix[o_zone][d_zone]
            volume_list.append(od_volume)
            o_zone_id_list.append(o_zone)
            d_zone_id_list.append(d_zone)
            geometry_list.append(str(line['geometry']))
            accessibility_list.append(line['accessibility'])

    data = pd.DataFrame(o_zone_id_list)
    data.columns = ["o_zone_id"]

    data["d_zone_id"] = pd.DataFrame(d_zone_id_list)
    data["accessibility"] = pd.DataFrame(accessibility_list)
    data["volume"] = pd.DataFrame(volume_list)
    data["geometry"] = pd.DataFrame(geometry_list)

    data.to_csv(r"demand.csv", index=False)


if __name__=='__main__':
    # Step 1: Get Network Information

    # Step 2: Read Input Data (node.csv and poi.csv)
    #file_chdir = os.getcwd()
    #os.chdir(file_chdir)
    g_ReadInputData()

    # Step 3: Network Partition
    g_network_partition()

    # Step 4: Output zone.csv and Update node.csv and poi.csv with zone_id
    g_output_zone()

    # Step 5: Get POI production/attraction rates of each poi type with a specific trip purpose and output poi_trip_rate.csv
    g_poi_demand()

    # Step 6: Define production/attraction value of each node according to POI type and update node.csv
    g_node_demand()

    # Step 7: Calculate Zone-to-zone Accessibility Matrix by Centroid-to-centroid Straight Distance
    g_access_mtrx()

    # Step 8: Apply Gravity Model to Conduct Trip Distribution
    gravity_model()

    print("End!")